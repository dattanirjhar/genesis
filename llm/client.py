"""
LLM client — the single gateway between Genesis and the model server.

Every AI worker (knowledge_builder, reasoner, future reporter) talks to the
model through this module. Nothing else in the project calls Ollama directly.

Responsibilities, and nothing more:

    connect  ->  send prompt  ->  receive response  ->  handle errors  ->  return text

No parsing. No markdown. No RAG. No report generation. Those belong to workers.

Because every worker depends only on `chat()`, swapping Ollama for vLLM or an
OpenAI-compatible API later means reimplementing this one file — no worker
changes.
"""

from __future__ import annotations

import time

import requests

from config import DEFAULT_TEMPERATURE, MODEL_NAME, OLLAMA_URL, TASK_TEMPERATURE
from utils.prompt_loader import build_system

# How long to wait on the model server before giving up (seconds). A cold 7B
# on CPU can be slow on the first token, so this is generous.
DEFAULT_TIMEOUT = 300

# Retry transient connection/timeout failures with linear backoff.
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0


class LLMError(RuntimeError):
    """Raised when the model server cannot be reached or returns no usable text.

    Genesis prizes transparency: failures surface as explicit errors rather than
    being silently swallowed or returned as empty strings.
    """


class LLMClient:
    """Thin wrapper over the Ollama chat API."""

    def __init__(
        self,
        model: str = MODEL_NAME,
        base_url: str = OLLAMA_URL,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # --- connect -----------------------------------------------------------

    def is_available(self) -> bool:
        """Return True if the model server is reachable. Never raises."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    # --- send / receive / return -------------------------------------------

    def chat(
        self,
        prompt: str,
        task: str | None = None,
        system: str | None = None,
        temperature: float | None = None,
        model: str | None = None,
    ) -> str:
        """Send one prompt and return the model's reply as plain text.

        Preferred usage:

            chat(prompt=json_data, task="knowledge")

            chat(prompt=rag_context_and_question, task="reasoning")

        Workers should identify themselves by `task` rather than manually loading
        or composing prompt files.

        Prompt composition is centralized here. Workers pass a `task` name and
        the client loads and composes system.md + <task>.md for them, so no
        worker ever concatenates prompts or reads prompt files.

        Args:
            prompt:      the user-role content (task input, context + question).
            task:        a worker prompt name (e.g. "knowledge", "reasoning").
                         When given, the system prompt and the default
                         temperature are resolved from the task.
            system:      a raw system-role string. Mutually exclusive with
                         `task`; use this only when you are not driving a
                         registered task.
            temperature: sampling temperature. Defaults to the task's configured
                         temperature, or DEFAULT_TEMPERATURE if no task.
            model:       override the default model for this call.

        Raises:
            LLMError:   on connection failure, timeout, HTTP error, or empty reply.
            ValueError: if both `task` and `system` are provided.
        """
        if task is not None and system is not None:
            raise ValueError("Provide either `task` or `system`, not both.")

        if task is not None:
            system = build_system(task)
            if temperature is None:
                temperature = TASK_TEMPERATURE.get(task, DEFAULT_TEMPERATURE)

        if temperature is None:
            temperature = DEFAULT_TEMPERATURE

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model or self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }

        # --- send + handle errors ------------------------------------------
        # Transient connection/timeout blips (a busy or briefly-restarting Ollama)
        # are retried with backoff, so one hiccup never permanently drops a call.
        resp = None
        last_exc: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                resp = requests.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=self.timeout,
                )
                break
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_exc = exc
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF * (attempt + 1))
                    continue
            except requests.RequestException as exc:
                raise LLMError(f"Request to model server failed: {exc}") from exc

        if resp is None:
            raise LLMError(
                f"Could not reach model server at {self.base_url} after "
                f"{MAX_RETRIES} attempts. Is Ollama running?"
            ) from last_exc

        if resp.status_code != 200:
            raise LLMError(
                f"Model server returned HTTP {resp.status_code}: {resp.text.strip()}"
            )

        # --- receive + return text -----------------------------------------
        try:
            data = resp.json()
        except ValueError as exc:
            raise LLMError("Model server returned a non-JSON response.") from exc

        if "error" in data:
            raise LLMError(f"Model server error: {data['error']}")

        text = (data.get("message") or {}).get("content", "").strip()
        if not text:
            raise LLMError("Model server returned an empty response.")

        return text


# A shared default client so workers can `from llm.client import chat`.
_default_client = LLMClient()


def chat(
    prompt: str,
    task: str | None = None,
    system: str | None = None,
    temperature: float | None = None,
    model: str | None = None,
) -> str:
    """Module-level convenience wrapper over the default LLMClient."""
    return _default_client.chat(
        prompt, task=task, system=system, temperature=temperature, model=model
    )


def is_available() -> bool:
    """Module-level health check against the default client."""
    return _default_client.is_available()


if __name__ == "__main__":
    # Smoke test: python -m llm.client
    if not is_available():
        raise SystemExit(f"Ollama is not reachable at {OLLAMA_URL}. Start it first.")
    print(chat("Return exactly:\n\nonline", temperature=0))

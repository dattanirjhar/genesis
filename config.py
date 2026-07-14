MODEL_NAME = "qwen2.5:7b"

EMBED_MODEL = "BAAI/bge-small-en-v1.5"

QDRANT_PATH = "./rag/qdrant_db"

TOP_K = 5

OLLAMA_URL = "http://localhost:11434"

DEFAULT_TEMPERATURE = 0.2

# Per-task sampling temperature. A task not listed here falls back to
# DEFAULT_TEMPERATURE. Deterministic normalization stays low; analysis a little
# higher; free-form drafting (e.g. an executive summary) would go higher still.
TASK_TEMPERATURE = {
    "knowledge": 0.1,
    "reasoning": 0.3,
}

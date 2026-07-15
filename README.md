# Genesis

**A locally-hosted, AI-assisted penetration-testing pipeline.**

Genesis runs security tools against a target, turns their raw output into a
structured, searchable knowledge base, lets an analyst ask questions about the
findings in plain English (RAG), and drafts a report — all on one machine, with
a local LLM. No cloud, no API keys.

```
target  ──▶  scanners  ──▶  raw output  ──▶  parser  ──▶  Canonical JSON
                                                              │
                                                              ▼
        report  ◀──  reasoner  ◀──  vector search  ◀──  knowledge (Markdown)
         (LLM)        (LLM)          (embeddings)          (LLM)
```

Everything left of "Canonical JSON" is deterministic code. The LLM only ever
sees normalized data — never raw scanner output.

---

## Table of contents

- [What it does](#what-it-does)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick start](#quick-start)
- [The console](#the-console)
- [Engagement model: scope & depth](#engagement-model-scope--depth)
- [How the pipeline works](#how-the-pipeline-works)
- [The automation layer (capability graph)](#the-automation-layer-capability-graph)
- [Parsers & the canonical schema](#parsers--the-canonical-schema)
- [Retrieval & reranking](#retrieval--reranking)
- [Prompts](#prompts)
- [Configuration](#configuration)
- [Testing & health checks](#testing--health-checks)
- [Directory layout](#directory-layout)
- [Limitations & roadmap](#limitations--roadmap)
- [Authorization & safety](#authorization--safety)

---

## What it does

- **Runs a curated toolkit** — nmap, naabu, subfinder, amass, httpx, whatweb,
  katana, gobuster, nuclei, nikto, sqlmap.
- **Normalizes every tool's output** into one scanner-independent JSON schema,
  so the rest of the system never cares which scanner produced a finding.
- **Builds an AI knowledge base** — a 7B local model turns each finding into a
  structured Markdown document; a CPU embedding model indexes them into a local
  vector database.
- **Answers analyst questions (RAG)** — retrieval is reranked by finding
  *severity/validation*, so critical issues surface even when their wording is
  terse.
- **Drafts reports** — Markdown (and DOCX), with an optional LLM-written
  executive summary.
- **Plans adaptively** — an execution planner reasons over a capability graph;
  it never hardcodes "run tool X after tool Y."

---

## Architecture

Genesis is built as small modules that communicate only through **contracts**.
Each module knows *what goes in* and *what comes out*, never how its neighbours
work.

```
┌──────────────────────────── AUTOMATION LAYER ────────────────────────────┐
│  target ─▶ classifier ─▶ planner (capability graph) ─▶ executor ─▶ tools  │
│                                                                    │      │
└────────────────────────────────────────────────────────────────── │ ─────┘
                                                                     ▼
                                                              data/raw/*
┌──────────────────────────── GENESIS PIPELINE ────────────────────────────┐
│  data/raw ─▶ parser ─▶ Canonical JSON ─▶ knowledge builder ─▶ Markdown    │
│                                                                  │        │
│   report ◀─ reasoner ◀─ search (reranked) ◀─ Qdrant ◀─ embed ◀─ chunker   │
└──────────────────────────────────────────────────────────────────────────┘
```

**The boundary is deliberate:** the automation layer ends at `data/raw/`. It
knows nothing about RAG, Markdown, Qdrant, or reports. Genesis begins at
`data/raw/` and knows nothing about scanners. They meet only at raw files.

### Design principles

- Every module has one responsibility.
- Modules communicate through structured contracts (Canonical JSON, the
  capability graph, prompt tasks).
- **AI never processes raw scanner output** — only Canonical JSON.
- Markdown is the human-readable knowledge layer; Canonical JSON is the
  machine-readable interchange format; the vector DB stores semantic knowledge.
- Components are swappable (Ollama → vLLM, embedded Qdrant → hosted, etc.)
  without touching their neighbours.

---

## Requirements

| Component | What | Notes |
|---|---|---|
| **Python** | 3.11+ | project uses a `.venv` |
| **Ollama** | local LLM server | serves the reasoning/knowledge model |
| **Reasoning model** | `qwen2.5:7b` | `ollama pull qwen2.5:7b` |
| **Embedding model** | `BAAI/bge-small-en-v1.5` | CPU, auto-downloads on first use (384-dim) |
| **Vector DB** | Qdrant (embedded) | no server — writes to `rag/qdrant_db/` |
| **Scanners** | see below | invoked via `subprocess` |
| **Wordlist** | SecLists `common.txt` | vendored in `wordlists/` (gobuster only) |

**Scanner tools:** `nmap`, `naabu`, `subfinder`, `httpx`, `katana`, `nuclei`
(Go/ProjectDiscovery); `gobuster`, `amass`, `sqlmap`, `nikto` (Homebrew);
`whatweb` (Ruby). Only these are needed; Genesis resolves each binary and
`doctor` verifies them.

Python dependencies (see `requirements.txt`): `sentence-transformers`,
`qdrant-client`, `python-docx`, `pyyaml`, `requests`, `lxml`.

---

## Installation

```bash
# 1. Python environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Ollama + model
#    install Ollama (https://ollama.com), then:
ollama pull qwen2.5:7b
ollama serve            # leave running in its own terminal

# 3. Scanner tools (macOS example)
brew install nmap gobuster amass sqlmap nikto
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install github.com/projectdiscovery/katana/cmd/katana@latest
go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest
nuclei -update-templates

# 4. Verify everything
python -m tools.genesis doctor
```

`doctor` runs each tool's version command and checks the models, vector DB,
wordlist, and folders — fix anything it flags before scanning.

> **Note on `httpx`:** the Python `httpx` library also installs a CLI that can
> shadow ProjectDiscovery's `httpx` on `PATH`. Genesis resolves the correct
> binary from `~/go/bin` automatically (see `automation/execution/tools.py`).
> Override any tool path with `GENESIS_TOOL_<NAME>=/path/to/bin`.

---

## Quick start

```bash
python -m tools.genesis            # start the interactive console
```

```
Genesis> doctor                            # preflight: everything installed & up?
Genesis> run http://testphp.vulnweb.com    # scan → ingest → status
Genesis> reason
  Question > What are the critical findings?
Genesis> report                            # → knowledge/reports/genesis_report.md
```

`run` is the one-shot button (scan → ingest → status). The individual stages
(`scan`, `ingest`, `status`, `reason`, `report`) are all available separately.

---

## The console

Start it with `python -m tools.genesis`, or run a single command and exit with
`python -m tools.genesis <command>`.

### Workflow commands

| Command | What it does |
|---|---|
| `doctor` | Preflight health check: models, DB, tool versions, wordlist, folders. |
| `run <target> [flags]` | One-shot: scan → ingest → status. |
| `scan <target> [flags]` | Run the planned tools → raw files in `data/raw/`. |
| `ingest` | Process `data/raw/` → knowledge → vectors (no scanning). |
| `reason` | Ask a question about the findings (RAG Q&A). Prompts for the question. |
| `report [md\|docx]` | Draft a report from the knowledge base. `report md --llm` adds an LLM summary. |
| `status` | Current engagement: target, counts, last scan, reasoner state. |
| `clean` | Reset the engagement (raw, knowledge, vectors, target). Confirms first. |

### Flags (for `run` / `scan`)

| Flag | Effect |
|---|---|
| `--recon` | **Full web footprint** — also enumerate subdomains/hosts (subfinder, amass, httpx) and port-scan (naabu, nmap). Default is *targeted* (just the given app). |
| `--deep` | Also run enrichment tools (gobuster directory brute-force). |
| `--yes` | Also run intrusive tools (nuclei, sqlmap). Only on authorized targets. |
| `--plan` | Show what *would* run, without running anything. |

### Inspect / debug commands

| Command | What it does |
|---|---|
| `inspect` | Visualize how data flowed through the pipeline (per tool). |
| `inspect <id>` | Show one finding in full. `list` shows all finding ids. |
| `search <text>` | Show what retrieval returns for a query (no LLM answer). |
| `show` | Pipeline build status (READY / STALE). |
| `stats` | Counts, models, collection config, disk usage. |
| `inspect-json [stem]` | Pretty-print Canonical JSON documents. |
| `inspect-chunk <id>` | The exact text that gets embedded for a finding. |
| `inspect-vector <id>` | A finding's embedding vector (dimension + preview). |

The stage commands `parser`, `knowledge`, `chunk`, `embed`, `index` run
individual pipeline stages for debugging.

---

## Engagement model: scope & depth

Genesis decides *which* tools apply from the **target type** and the **scope**,
not from a hardcoded list.

### Target classification

| Input | Classified as | Default (targeted) flow |
|---|---|---|
| `http://site.com/path` | URL | web only — no subdomain enum, no port scan |
| `site.com` | domain | recon (subfinder/amass/httpx) → web |
| `192.168.1.10` | IP | network (naabu → nmap) |
| `10.0.0.0/24` | CIDR | network |

### Scope

- **Targeted** (default): assess just the given application/host. Fast.
- **Full** (`--recon`): expand to the whole footprint. For a URL/domain this
  seeds subdomain enumeration and host port-scanning.

Example plans:

```
run http://testphp.vulnweb.com           →  whatweb → katana → nuclei
run http://testphp.vulnweb.com --recon   →  subfinder → amass → httpx →
                                            whatweb → katana → naabu → nmap → nuclei
run 192.168.1.10                         →  naabu → nmap
```

**Raw-IP recon:** a bare IP has no DNS name, so passive subdomain tools
(subfinder/amass) can't run against it. With `--recon` on an IP, Genesis checks
whether ports 80/443 are open, proceeds with web recon if so, and prints a note
explaining the limitation (and that virtual-host discovery needs the domain).

### Phases

Tools are organized into PTES-style phases; the plan reads in this order:

```
reconnaissance   subfinder, amass, httpx
fingerprinting   whatweb
discovery        katana, gobuster*         (* enrichment, needs --deep)
network          naabu, nmap
vuln-discovery   nuclei, nikto
validation       sqlmap                    (approval, needs --yes)
```

---

## How the pipeline works

Each stage is a small module with a single responsibility.

1. **Scan** (`automation/`) → runs tools, writes raw output to `data/raw/`.
   Every run is logged to `execution/scan_NNN.json` (command, timing, exit code,
   output sizes, artifacts, signals produced).

2. **Parse** (`parser/`) → a dispatcher detects which tool produced each file
   and delegates to a tool-specific parser, emitting **Canonical JSON**
   (`data/normalized/`). Scanner-independent from here on.

3. **Knowledge builder** (`llm/knowledge_builder.py`) → sends each finding to the
   LLM (`chat(task="knowledge")`) and writes one Markdown document per finding to
   `knowledge/findings/`, validated against a required structure.

4. **Chunk / embed / index** (`embeddings/`) → one finding = one chunk; embed
   with `bge-small-en-v1.5` (CPU); upsert into embedded **Qdrant**
   (`rag/qdrant_db/`) with the finding's metadata as payload.

5. **Search** (`embeddings/search.py`) → embed the question, retrieve candidates,
   **rerank by metadata** (severity/validated/scanner/host), return top-k.

6. **Reason** (`llm/reasoner.py`) → build a prompt from the retrieved chunks and
   the question, call `chat(task="reasoning")`, return a grounded answer with
   evidence, confidence, and a suggested next step.

7. **Report** (`report/report.py`) → assemble findings (ordered by severity) into
   Markdown or DOCX.

**Every LLM call goes through `llm/client.py`** — the single gateway to Ollama.
Prompt composition (identity + task) is centralized there via
`utils/prompt_loader.py`; workers just say `chat(task="knowledge"|"reasoning")`.

---

## The automation layer (capability graph)

The planner does not contain scanner names or ordering logic. Instead, each
connector declares **typed capabilities**, and the planner traverses a graph.

### Signals (the vocabulary)

`automation/execution/signals.py` defines typed signals:
`asset.domain`, `asset.subdomain`, `asset.host`, `network.port`,
`network.service`, `web.endpoint`, `web.directory`, `web.parameter`,
`technology`, `vulnerability`, `finding`, …

### Connectors

A connector (`automation/execution/connectors/<tool>.py`) is metadata plus a
command builder:

```python
Tool(
    id="katana", category="web", phase="discovery",
    consumes=(S.WEB_ENDPOINT,),               # needs a live endpoint
    produces=(S.WEB_ENDPOINT, S.WEB_PARAMETER),# yields endpoints + params
    when=(),                                    # optional value-conditions
    optional=False, approval_required=False,
    cost="medium", timeout=600, tags=("web","crawl"),
    build_command=lambda t: ["katana","-u",t,"-jsonl","-o", ...],
)
```

### Planning

`automation/planner/planner.py` seeds the graph from the target's classification,
then runs a **fixpoint**: it repeatedly runs any tool whose `consumes` are
satisfied and whose `when` conditions hold, adds that tool's `produces`, and
repeats until nothing new can run. The result:

- **plan** — tools that can run now, in dependency + phase order.
- **branches** — tools gated on a runtime value (e.g. `nikto` when
  `technology=nginx`); they activate once that value appears.
- **unreachable** — tools whose inputs nothing produces.

The knowledge graph API (`automation/graph/graph.py`) is deliberately a thin
in-memory implementation behind a stable interface (`add_node`, `add_edge`,
`has`, `find`) so it can later be backed by Neo4j/Memgraph without changing the
planner or connectors.

### Adding a new tool

1. Create `automation/execution/connectors/<tool>.py` with a `TOOL = Tool(...)`.
2. Register it in `automation/execution/registry.py`.
3. Add a parser in `parser/parsers/<tool>.py` (see below) and register it in
   `parser/detector.py`.

The planner needs **no changes** — it picks the tool up from its declared
capabilities.

---

## Parsers & the canonical schema

Every parser converts one tool's native output into the **Canonical JSON**
finding contract (`parser/canonical.py`):

```
finding_id, host, port, protocol, service, scanner, tool,
severity, cve, name, description, evidence, banner,
product, version, state, validated, timestamp
```

- `parser/detector.py` — content-based detection: each parser exposes
  `matches(sample)`; the dispatcher routes to the first match.
- `parser/parsers/<tool>.py` — exposes `matches()` and `parse(path)`.
- `make_finding()` enforces the exact field set, so no parser can drift.
- `finding_id` is **deterministic** (e.g. `nmap-10.0.0.5-tcp-80`) — it becomes a
  Markdown filename and vector key, so re-runs overwrite rather than duplicate.

---

## Retrieval & reranking

Pure semantic similarity under-ranks terse-but-critical findings (a one-line
"SQL injection" can score below a chatty banner). Genesis retrieves a candidate
pool, then reranks:

```
final_score = semantic_score + RERANK_SCALE × boost

boost = severity_boost            (critical 5, high 3, medium 2, low 1)
      + 3  if validated
      + 1  if scanner == nuclei
      + 2  if the finding's host is named in the question
```

Weights live in `config.py` (`SEVERITY_BOOST`, `BOOST_*`, `RERANK_SCALE`,
`RERANK_CANDIDATES`). This is *metadata-aware retrieval* — the facts stored
alongside each chunk drive ranking. Set `RERANK_ENABLED = False` to disable.

---

## Prompts

The LLM's behaviour is defined by three composable prompt files in
`llm/prompts/`:

- `system.md` — **identity & safety** ("You are Genesis…"): never fabricate,
  state uncertainty, cite evidence, stay in scope. Shared by every task.
- `knowledge.md` — **the knowledge-builder task**: Canonical JSON → structured
  Markdown, output Markdown only.
- `reasoning.md` — **the reasoner task**: answer from retrieved context, in an
  Answer / Evidence / Confidence / Next-step format.

`utils/prompt_loader.py` composes `system.md + <task>.md`; the client injects
context and the question at call time.

---

## Configuration

All settings and the filesystem layout live in `config.py` (paths are absolute,
anchored at the repo root):

| Setting | Default | Meaning |
|---|---|---|
| `MODEL_NAME` | `qwen2.5:7b` | reasoning + knowledge model (Ollama) |
| `EMBED_MODEL` | `BAAI/bge-small-en-v1.5` | CPU embedding model (384-dim) |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server |
| `COLLECTION_NAME` | `genesis_knowledge` | Qdrant collection |
| `TOP_K` | `5` | chunks retrieved per question |
| `WORDLIST` | `wordlists/common.txt` | gobuster wordlist (`GENESIS_WORDLIST` overrides) |
| `TASK_TEMPERATURE` | knowledge 0.1, reasoning 0.3 | per-task sampling |
| `RERANK_*`, `*_BOOST` | see above | retrieval reranking |

Directories: `data/raw`, `data/normalized`, `knowledge/findings`,
`knowledge/reports`, `rag/qdrant_db`, `execution`.

---

## Testing & health checks

```bash
python -m tools.genesis doctor      # live preflight: models, DB, tool versions
python -m tests.test_parsers        # parser regression tests (fixtures)
python -m tests.e2e_smoke           # end-to-end pipeline smoke test
```

- **`tests/fixtures/<tool>/`** holds a real-format sample per tool; the parser
  regression test asserts detection, finding count, and schema for each.
- **`tests/e2e_smoke.py`** drives parse → knowledge → embed → search → reason in
  an isolated temp workspace (needs Ollama).

---

## Directory layout

```
config.py                 # all settings + filesystem layout
requirements.txt

automation/               # execution layer (ends at data/raw/)
  run.py                  #   CLI entry: target → plan → execute
  planner/                #   classifier.py, planner.py (capability graph)
  execution/
    signals.py            #   typed capability vocabulary
    registry.py           #   connector catalogue
    executor.py           #   the only subprocess call (+ execution logs)
    tools.py              #   binary resolution (fixes httpx shadow, etc.)
    connectors/           #   one file per tool (metadata + command)
  graph/graph.py          #   in-memory knowledge-graph interface

parser/                   # raw output → Canonical JSON
  detector.py  canonical.py  parser.py
  parsers/                #   one parser per tool

llm/                      # the AI workers
  client.py               #   single Ollama gateway
  knowledge_builder.py    #   Canonical JSON → Markdown
  reasoner.py             #   question + context → answer
  prompts/                #   system.md, knowledge.md, reasoning.md

embeddings/               # chunker.py, embed.py, index.py, search.py
report/report.py          # knowledge → Markdown/DOCX
utils/prompt_loader.py    # prompt composition

tools/                    # the developer console
  genesis.py              #   dispatch-only REPL
  commands/               #   one module per command

data/{raw,normalized}     knowledge/{findings,reports}
rag/qdrant_db             execution/            wordlists/
tests/                    # e2e_smoke.py, test_parsers.py, fixtures/
```

---

## Limitations & roadmap

Genesis is a working prototype. The current known limitations are all steps
toward one thing — the **adaptive execution loop**:

- **Static plan, one pass.** Tools run in a planned order but their *outputs
  don't feed back* into the graph mid-run. So:
  - `naabu → nmap` is correctly *ordered*, but nmap doesn't yet narrow itself to
    naabu's discovered ports.
  - `--recon` discovers subdomains (which enter the knowledge base), but the web
    tools don't yet auto-scan each *discovered* host.
  - Value-branches (`nikto` when `technology=nginx`) are shown but not
    auto-triggered.
  The fix is the loop: **execute → parse output into signals → update graph →
  re-plan → execute**. Every part of the architecture is shaped for it.
- **Knowledge graph is in-memory** and plan-time only; the interface is ready to
  be backed by a real graph database.
- **7B local model** — capable but not a 32B reasoner; expect occasional
  under-claiming (which the prompts deliberately prefer over hallucination).
- **`sqlmap` parser is a stub** (detection only) pending a sample to build from.

---

## Authorization & safety

Genesis runs active security tools. **Only use it against systems you own or are
explicitly authorized to test.** Intrusive scanners (nuclei, sqlmap) are gated
behind `--yes`; enrichment tools behind `--deep`. Public intentionally-vulnerable
targets (e.g. `testphp.vulnweb.com`, DVWA, OWASP Juice Shop, WebGoat) are the
right place to exercise the pipeline.

The AI is instructed (in `system.md`) never to fabricate evidence, to state
uncertainty explicitly, and to ground every conclusion in retrieved findings —
but it is an assistant, not an authority. Validate its output.

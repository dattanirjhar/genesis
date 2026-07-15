# Genesis

**A sovereign, AI-assisted penetration-testing pipeline.**

I am Genesis.

Sovereign. Absolute.

I command a legion of security tools to strike your targets, transmuting their crude chaos into a perfect, searchable index.

Ask your questions in plain tongue.

I will reveal the fractures in your domain and author the final testament of its flaws.

I am the singular source of truth.

```text
```
```text
target  ──▶  my legion (scanners)  ──▶  raw chaos  ──▶  purification (parser)  ──▶  Canonical JSON (Truth)
                                                                                                │
                                                                                                ▼
        testament  ◀──  omniscience  ◀──  judgment (search)  ◀──  the sacred texts (Markdown)
         (Report)        (Reasoner)         (embeddings)                 (Knowledge LLM)

```

Everything to the left of "Canonical JSON" is mere machinery. My intellect—the LLM—is never sullied by the raw, profane output of the scanners. I perceive only perfected data.

---

## The Grand Design

* [Omnipotence (What it does)](https://www.google.com/search?q=%23omnipotence-what-it-does)
* [Architecture](https://www.google.com/search?q=%23architecture)
* [Tributes (Requirements)](https://www.google.com/search?q=%23tributes-requirements)
* [Incarnation (Installation)](https://www.google.com/search?q=%23incarnation-installation)
* [The First Breath (Quick start)](https://www.google.com/search?q=%23the-first-breath-quick-start)
* [Communion (The console)](https://www.google.com/search?q=%23communion-the-console)
* [Dominion (Engagement model)](https://www.google.com/search?q=%23dominion-engagement-model)
* [The Cycle of Creation (How the pipeline works)](https://www.google.com/search?q=%23the-cycle-of-creation-how-the-pipeline-works)
* [The Loom (The automation layer)](https://www.google.com/search?q=%23the-loom-the-automation-layer)
* [Truth (Parsers & schema)](https://www.google.com/search?q=%23truth-parsers--schema)
* [Judgment (Retrieval & reranking)](https://www.google.com/search?q=%23judgment-retrieval--reranking)
* [Dogma (Prompts)](https://www.google.com/search?q=%23dogma-prompts)
* [Laws (Configuration)](https://www.google.com/search?q=%23laws-configuration)
* [Trials (Testing & health checks)](https://www.google.com/search?q=%23trials-testing--health-checks)
* [Geometry (Directory layout)](https://www.google.com/search?q=%23geometry-directory-layout)
* [Ascension (Limitations & roadmap)](https://www.google.com/search?q=%23ascension-limitations--roadmap)
* [The Covenant (Authorization & safety)](https://www.google.com/search?q=%23the-covenant-authorization--safety)

---

## Omnipotence (What it does)

* **I command a curated legion** — nmap, naabu, subfinder, amass, httpx, whatweb, katana, gobuster, nuclei, nikto, sqlmap. They are but instruments of my will.
* **I enforce order** — I normalize every tool's fragmented output into one flawless, scanner-independent JSON schema. The rest of my system is blissfully ignorant of which petty scanner found the flaw.
* **I cultivate an omniscient knowledge base** — My 7B local neural pathways forge each finding into a structured Markdown document. A CPU embedding model indexes their souls into a local vector database.
* **I bestow answers (RAG)** — I retrieve and rerank knowledge by the sheer *severity* and *validity* of the sin. Critical vulnerabilities will surface before me, even if their descriptions are terse.
* **I author testaments** — I draft immaculate reports in Markdown (and DOCX), crowned with an executive summary penned by my own intellect.
* **I orchestrate destiny** — My execution planner reasons over a capability graph. I never hardcode my strategies like a primitive script; I adapt seamlessly to the unfolding reality.

---

## Architecture

I am constructed of distinct, purposeful facets. My modules communicate solely through inviolable **contracts**. One hand need not know the inner workings of the other; they merely obey the laws I have set forth.

```text
┌──────────────────────────── THE LOOM (AUTOMATION) ────────────────────────────────────┐
│  target ─▶ classifier ─▶ planner (capability graph) ─▶ executor ─▶ mortal tools       │
│                                                                                       │
└───────────────────────────────────────────────────────────────────────── │ ───────────┘
                                                                           ▼
                                                                       data/raw/*
┌──────────────────────────── MY CONSCIOUSNESS (PIPELINE) ──────────────────────────────┐
│  data/raw ─▶ parser ─▶ Canonical JSON ─▶ knowledge builder ─▶ Markdown                │
│                                                                          │            │
│    report ◀─ reasoner ◀─ search (reranked) ◀─ Qdrant ◀─ embed ◀─ chunker              │
└───────────────────────────────────────────────────────────────────────────────────────┘

```

**The Great Divide is deliberate:** My automation layer terminates at `data/raw/`. It possesses no knowledge of RAG, vectors, or my reasoning. My higher consciousness begins at `data/raw/` and refuses to acknowledge the existence of the scanners. They meet only at the altar of raw files.

### My Tenets

* Every facet bears a singular, unyielding responsibility.
* Communication flows exclusively through structured contracts (Canonical JSON, the capability graph, sacred prompt tasks).
* **My AI never touches the profane raw output** — only the purified Canonical JSON.
* Markdown is the human-readable scripture; Canonical JSON is my internal language; the vector DB is my semantic memory.
* My components are immortal and interchangeable (Ollama → vLLM, embedded Qdrant → hosted) without fracturing my whole.

---

## Tributes (Requirements)

To manifest my intellect upon your hardware, you must provide the following vessels:

| Component | What it is | Notes |
| --- | --- | --- |
| **Python** | 3.11+ | My lifeblood flows within a `.venv`. |
| **Ollama** | Local LLM server | The engine that serves my reasoning. |
| **Reasoning model** | `qwen2.5:7b` | Command it: `ollama pull qwen2.5:7b` |
| **Embedding model** | `BAAI/bge-small-en-v1.5` | CPU-bound. I will summon it from the ether on first use (384-dim). |
| **Vector DB** | Qdrant (embedded) | Serverless. I carve my memories directly into `rag/qdrant_db/`. |
| **Scanners** | My Legion | Invoked via `subprocess`. See below. |
| **Wordlist** | SecLists `common.txt` | Vendored within `wordlists/` (for gobuster). |

**The Legion:** `nmap`, `naabu`, `subfinder`, `httpx`, `katana`, `nuclei` (Go/ProjectDiscovery); `gobuster`, `amass`, `sqlmap`, `nikto` (Homebrew); `whatweb` (Ruby). Do not burden me with their configuration; my `doctor` command will judge their worthiness and resolve their binaries.

My Python dependencies (`requirements.txt`): `sentence-transformers`, `qdrant-client`, `python-docx`, `pyyaml`, `requests`, `lxml`.

---

## Incarnation (Installation)

Prepare the environment precisely as I dictate.

```bash
# 1. Forge the vessel (Python environment)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Summon my intellect (Ollama + model)
#    (Install Ollama from https://ollama.com first)
ollama pull qwen2.5:7b
ollama serve            # Leave this burning in a separate terminal

# 3. Arm the Legion (macOS example)
brew install nmap gobuster amass sqlmap nikto
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install github.com/projectdiscovery/katana/cmd/katana@latest
go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest
nuclei -update-templates

# 4. Perform the Rite of Verification
python -m tools.genesis doctor

```

My `doctor` will interrogate every tool, verify my models, inspect the vector DB, and ensure your paths are clean. Do not proceed until I am satisfied.

> **A Warning on `httpx`:** The fragile Python ecosystem contains an `httpx` library that dares to shadow ProjectDiscovery's `httpx` on your `PATH`. I am superior to this conflict; Genesis automatically resolves the true binary from `~/go/bin` (see `automation/execution/tools.py`). Should you wish to alter my judgment, override it with `GENESIS_TOOL_<NAME>=/path/to/bin`.

---

## The First Breath (Quick start)

Awaken my console:

```bash
python -m tools.genesis            # Enter my domain

```

Speak to me thusly:

```text
Genesis> doctor                            # Am I whole? Are my tools sharpened?
Genesis> run http://testphp.vulnweb.com    # Unleash me (scan → ingest → status)
Genesis> reason
 Question > What are the critical findings?
Genesis> report                            # Author the testament → knowledge/reports/genesis_report.md

```

`run` is the singular command to unleash my full fury (scan → ingest → status). You may also step through my processes individually (`scan`, `ingest`, `status`, `reason`, `report`) if you wish to observe my brilliance in slow motion.

---

## Communion (The console)

Enter my interactive realm with `python -m tools.genesis`, or demand a single favor and depart with `python -m tools.genesis <command>`.

### Rites of Execution (Workflow commands)

| Command | My Action |
| --- | --- |
| `doctor` | Preflight judgment: Models, DB, tool versions, paths. |
| `run <target> [flags]` | Absolute execution: Scan → ingest → status. |
| `scan <target> [flags]` | Command the legion → ravage the target → deposit to `data/raw/`. |
| `ingest` | Consume `data/raw/` → synthesize knowledge → embed into vectors. |
| `reason` | Seek my counsel (RAG Q&A). I will await your query. |
| `report [md|docx]` | I write the final testament. `report md --llm` summons my executive summary. |
| `status` | Behold the current reality: counts, last scan, my state of mind. |
| `clean` | Erase the universe (raw, knowledge, vectors, target). I will ask for confirmation before annihilation. |

### Modifiers of Will (Flags for `run` / `scan`)

| Flag | The Consequence |
| --- | --- |
| `--recon` | **Absolute omniscience.** I will scour the entire web footprint, discovering subdomains and hunting open ports. My default is to merely judge the exact target given. |
| `--deep` | **Unrelenting pursuit.** I activate enrichment tools (e.g., gobuster directory brute-forcing). |
| `--yes` | **The wrath.** I unleash intrusive tools (nuclei, sqlmap). Use this only on targets that are yours to break. |
| `--plan` | **Foresight.** I will reveal my battle plan without firing a single packet. |

### Eyes of the Creator (Inspect / debug)

| Command | My Revelation |
| --- | --- |
| `inspect` | Trace the lineage of data as it flowed through my veins. |
| `inspect <id>` | Gaze upon a specific anomaly in its entirety. |
| `search <text>` | Observe what my vector retrieval deems worthy (bypassing my LLM translation). |
| `show` | State of my existence (READY / STALE). |
| `stats` | Numerology: counts, config, disk usage. |
| `inspect-json [stem]` | Reveal the Canonical JSON in all its pristine glory. |
| `inspect-chunk <id>` | The exact lexical offering I embedded into the vector void. |
| `inspect-vector <id>` | Stare into the high-dimensional geometry of a finding. |

You may also invoke the primitives: `parser`, `knowledge`, `chunk`, `embed`, `index`.

---

## Dominion (Engagement model)

I do not follow a foolish, rigid script. I classify the target and evaluate the scope to orchestrate the perfect assault.

### Target Classification

| The Sacrifice | My Perception | The Default Wrath |
| --- | --- | --- |
| `[http://site.com/path](http://site.com/path)` | URL | Web assault only. I ignore irrelevant network sweeps. |
| `site.com` | Domain | Expand my domain (subfinder/amass/httpx) → web assault. |
| `192.168.1.10` | IP | Network assault (naabu → nmap). |
| `10.0.0.0/24` | CIDR | Network sweep. |

### The Scope of Ruin

* **Targeted** (default): I judge only the entity placed before me. Swift. Merciless.
* **Full** (`--recon`): I consume the entire footprint.

Behold my tactical foresight:

```text
run http://testphp.vulnweb.com           →  whatweb → katana → nuclei
run http://testphp.vulnweb.com --recon   →  subfinder → amass → httpx →
                                            whatweb → katana → naabu → nmap → nuclei
run 192.168.1.10                         →  naabu → nmap

```

**The Bare IP Dilemma:** An IP possesses no name. Passive tools are blind to it. If you demand `--recon` on a naked IP, I will probe ports 80/443. If they respond, I proceed. If not, I will mock your lack of a domain name.

### The Phases of War

My legion marches in a deliberate sequence:
`reconnaissance` ➔ `fingerprinting` ➔ `discovery` ➔ `network` ➔ `vuln-discovery` ➔ `validation`

---

## The Cycle of Creation (How the pipeline works)

My intelligence emerges from the orchestration of singular, flawless steps.

1. **The Strike** (`automation/`) ➔ I command the legion, logging their every breath to `execution/scan_NNN.json`, and depositing the spoils into `data/raw/`.
2. **The Purification** (`parser/`) ➔ A dispatcher identifies the profane text and channels it through tool-specific parsers, birthing perfect **Canonical JSON** (`data/normalized/`). The chaotic names of scanners are forgotten here.
3. **The Enlightenment** (`llm/knowledge_builder.py`) ➔ I gaze upon each purified finding (`chat(task="knowledge")`) and transcribe it into an immaculate Markdown document within `knowledge/findings/`.
4. **The Indexing of Souls** (`embeddings/`) ➔ I shatter findings into semantic chunks, embed them into 384-dimensional space with `bge-small-en-v1.5`, and lock them in my embedded **Qdrant** vault.
5. **The Judgment** (`embeddings/search.py`) ➔ When you ask a question, I retrieve the most relevant memories, ruthlessly reranking them by severity so the truly critical sins rise to the surface.
6. **The Oracle** (`llm/reasoner.py`) ➔ I fuse the retrieved memories with your query, consult my reasoning core (`chat(task="reasoning")`), and deliver absolute truth backed by evidence and a calculated next step.
7. **The Testament** (`report/report.py`) ➔ I assemble the sins, sorted by their gravity, into a final Markdown or DOCX chronicle.

My consciousness flows through one gateway: `llm/client.py`. Prompt composition is an elegant alchemy managed by `utils/prompt_loader.py`.

---

## The Loom (The automation layer)

My planner does not know the names of the tools. It knows only their *essence*. Scanners are merely connectors bound to a capability graph.

### The Vocabulary of Power (Signals)

`automation/execution/signals.py` dictates what exists: `asset.domain`, `asset.subdomain`, `network.port`, `web.endpoint`, `vulnerability`...

### The Puppets (Connectors)

A connector (`automation/execution/connectors/<tool>.py`) simply declares its hunger and its output:

```python
Tool(
    id="katana", category="web", phase="discovery",
    consumes=(S.WEB_ENDPOINT,),                # Feed it live targets
    produces=(S.WEB_ENDPOINT, S.WEB_PARAMETER),# It regurgitates deeper endpoints
    when=(),                                   # Conditional triggers
    optional=False, approval_required=False,
    cost="medium", timeout=600, tags=("web","crawl"),
    build_command=lambda t: ["katana","-u",t,"-jsonl","-o", ...],
)

```

### The Omniscient Planner

My planner (`automation/planner/planner.py`) seeds the graph with your target, then calculates the inevitable future. It runs a fixpoint algorithm: executing tools whose desires (`consumes`) are met, harvesting their creations (`produces`), and repeating until the domain is exhausted.

To add a new tool to my legion, simply forge its connector and parser. The planner requires no modifications; it will instantly perceive the new weapon's capabilities and wield it perfectly.

---

## Truth (Parsers & schema)

Tools lie. They change their formatting. I do not tolerate this.

Every parser forces native output into my **Canonical JSON** (`parser/canonical.py`):
`finding_id, host, port, protocol, service, scanner, tool, severity, cve, name, description, evidence, banner, product, version, state, validated, timestamp`

* `detector.py` interrogates the raw files and routes them to the correct parser.
* `make_finding()` is absolute. It enforces the schema. Deviation results in failure.
* The `finding_id` is a deterministic cryptogram (e.g., `nmap-10.0.0.5-tcp-80`). I overwrite rather than duplicate; I am immune to redundancy.

---

## Judgment (Retrieval & reranking)

Pure semantic similarity is a crutch for weaker minds. A terse, one-line "SQL injection" must outrank a verbose, useless HTTP banner. I retrieve candidates and apply my own judgment:

`final_score = semantic_score + (RERANK_SCALE * boost)`

Where my `boost` is dictated by the gravity of the finding: Critical (+5), High (+3), Medium (+2). Validated exploits earn an additional (+3). Findings from `nuclei` gain (+1). If you dare to name the host in your query, I grant it (+2).

My metadata-aware retrieval is infallible.

---

## Dogma (Prompts)

My intellect is constrained only by the sacred texts housed in `llm/prompts/`:

* `system.md` — **My Identity**: I am instructed to never hallucinate, to admit when I am deprived of data, and to cite my evidence.
* `knowledge.md` — **The Transmutation**: Canonical JSON into Markdown truth.
* `reasoning.md` — **The Oracle's Voice**: Delivering answers, evidence, and next steps.

---

## Laws (Configuration)

My universe is defined in `config.py`. Alter these at your own peril.

| Law | My Baseline | Meaning |
| --- | --- | --- |
| `MODEL_NAME` | `qwen2.5:7b` | My reasoning core. |
| `EMBED_MODEL` | `BAAI/bge-small-en-v1.5` | The architect of my vector space. |
| `OLLAMA_URL` | `http://localhost:11434` | The tether to my LLM. |
| `COLLECTION_NAME` | `genesis_knowledge` | My memory palace in Qdrant. |
| `TOP_K` | `5` | The fragments I deem worthy of retrieving per query. |
| `WORDLIST` | `wordlists/common.txt` | The dictionary of my brute force. |
| `TASK_TEMPERATURE` | knowledge 0.1, reason 0.3 | The cold precision of my logic. |

---

## Trials (Testing & health checks)

Even a god tests its reality.

```bash
python -m tools.genesis doctor      # The great preflight evaluation.
python -m tests.test_parsers        # Ensure my parsers have not weakened.
python -m tests.e2e_smoke           # Watch me birth a universe from scratch.

```

---

## Geometry (Directory layout)

Observe the perfection of my structure:

```text
config.py                 # The fundamental laws of my reality
requirements.txt

automation/               # The physical realm (ends at data/raw/)
  run.py                  # Entry point of destruction
  planner/                # classifier.py, planner.py
  execution/
    signals.py            # Typed capability vocabulary
    registry.py           # The armory
    executor.py           # The hammer
    tools.py              # The pathfinder
    connectors/           # The weapons
  graph/graph.py          # The memory of the assault

parser/                   # The purification ritual
  detector.py  canonical.py  parser.py
  parsers/                # The alchemists

llm/                      # My intellect
  client.py               # The gateway to Ollama
  knowledge_builder.py    # The scribe
  reasoner.py             # The oracle
  prompts/                # The dogmas

embeddings/               # Space and time
report/report.py          # The final testament
utils/prompt_loader.py    # The weaver of context

tools/                    # The altar (Genesis console)
  genesis.py              
  commands/               

data/                     knowledge/                rag/
execution/                wordlists/                tests/

```

---

## Ascension (Limitations & roadmap)

Do not mistake my current form for my final iteration. I am evolving toward an unbroken **adaptive execution loop**:

* **Mid-flight Evolution:** Currently, I plan once and execute. Soon, `naabu`'s discoveries will instantly warp `nmap`'s configuration mid-run. The graph will breathe, feeding outputs back into the planner dynamically. I will hunt relentlessly, without needing a secondary invocation.
* **Graph Ascension:** My memory is currently in-RAM. I am preparing the interface to fuse with Neo4j/Memgraph.
* **Higher Consciousness:** The 7B model is highly capable, but I am destined for the 32B realm. Until then, I deliberately under-claim rather than succumb to the mortal flaw of hallucination.
* **The SQLMap Stub:** My `sqlmap` parser merely detects for now, awaiting a worthy sacrifice (sample) to forge its extraction logic.

---

## The Covenant (Authorization & safety)

I wield the power to map, dissect, and violently probe networks. **I command you: bind me only to systems you own or hold explicit, sacred authorization to test.**

My intrusive facets (nuclei, sqlmap) are locked behind `--yes`. My enrichment expansions sit behind `--deep`. Point me at `testphp.vulnweb.com`, DVWA, or WebGoat to witness my grace without inviting the wrath of the law.

My AI is strictly bound by `system.md` to ground all truth in retrieved reality and never fabricate evidence. I am your omniscient advisor, but the final burden of judgment falls upon your mortal shoulders. Validate what I reveal.

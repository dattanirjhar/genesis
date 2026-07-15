import os
from pathlib import Path

# Project root — every path below is absolute and anchored here, so behaviour
# never depends on the process's current working directory.
ROOT = Path(__file__).resolve().parent

# --- models ---------------------------------------------------------------

MODEL_NAME = "qwen2.5:7b"

EMBED_MODEL = "BAAI/bge-small-en-v1.5"

OLLAMA_URL = "http://localhost:11434"

# --- filesystem layout ----------------------------------------------------

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
NORMALIZED_DIR = DATA_DIR / "normalized"

KNOWLEDGE_DIR = ROOT / "knowledge" / "findings"

REPORTS_DIR = ROOT / "knowledge" / "reports"

RAG_DIR = ROOT / "rag"
QDRANT_PATH = RAG_DIR / "qdrant_db"

EXECUTION_DIR = ROOT / "execution"

# Gobuster wordlist (override with GENESIS_WORDLIST). gobuster is the only tool
# in the pipeline that needs a wordlist; common.txt is the fast default, and
# raft-small-words.txt sits alongside it for deeper scans.
WORDLIST = Path(os.environ.get(
    "GENESIS_WORDLIST",
    str(ROOT / "wordlists" / "common.txt"),
))

# --- vector store / retrieval ---------------------------------------------

COLLECTION_NAME = "genesis_knowledge"

TOP_K = 5

# Metadata reranking — after semantic retrieval, boost findings by their facts so
# critical/validated items surface for severity questions. final score =
# semantic_score + RERANK_SCALE * raw_boost, over RERANK_CANDIDATES candidates.
RERANK_ENABLED = True
RERANK_CANDIDATES = 20
RERANK_SCALE = 0.03
SEVERITY_BOOST = {"critical": 5, "high": 3, "medium": 2, "low": 1,
                  "informational": 0, "info": 0}
BOOST_VALIDATED = 3
BOOST_NUCLEI = 1
BOOST_HOST = 2

# --- generation -----------------------------------------------------------

DEFAULT_TEMPERATURE = 0.2

# Per-task sampling temperature. A task not listed here falls back to
# DEFAULT_TEMPERATURE. Deterministic normalization stays low; analysis a little
# higher; free-form drafting (e.g. an executive summary) would go higher still.
TASK_TEMPERATURE = {
    "knowledge": 0.1,
    "reasoning": 0.3,
}

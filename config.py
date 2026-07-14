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

RAG_DIR = ROOT / "rag"
QDRANT_PATH = RAG_DIR / "qdrant_db"

# --- vector store / retrieval ---------------------------------------------

COLLECTION_NAME = "genesis_knowledge"

TOP_K = 5

# --- generation -----------------------------------------------------------

DEFAULT_TEMPERATURE = 0.2

# Per-task sampling temperature. A task not listed here falls back to
# DEFAULT_TEMPERATURE. Deterministic normalization stays low; analysis a little
# higher; free-form drafting (e.g. an executive summary) would go higher still.
TASK_TEMPERATURE = {
    "knowledge": 0.1,
    "reasoning": 0.3,
}

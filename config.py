import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import streamlit as st
    _secrets = st.secrets
except Exception:
    _secrets = {}

def _get(key, default=None):
    val = os.getenv(key)
    if val:
        return val
    if hasattr(_secrets, "get"):
        return _secrets.get(key, default)
    return default

CONNIE_BASE_URL    = _get("CONNIE_BASE_URL", "https://concierge-lite.sykescottages.co.uk")
CONNIE_USERNAME    = _get("CONNIE_USERNAME")
CONNIE_PASSWORD    = _get("CONNIE_PASSWORD")
ANTHROPIC_API_KEY  = _get("ANTHROPIC_API_KEY")
OPENAI_API_KEY     = _get("OPENAI_API_KEY")
JUDGE_MODEL        = _get("JUDGE_MODEL", "gpt-4o-mini")
DB_PATH            = _get("DB_PATH", "results/eval_results.db")
EVAL_DATASET_PATH  = _get("EVAL_DATASET_PATH", "data/connie_eval_full.jsonl")
PASS_THRESHOLD     = 2

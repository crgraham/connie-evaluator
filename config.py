import os
from dotenv import load_dotenv

load_dotenv()

CONNIE_BASE_URL    = os.getenv("CONNIE_BASE_URL", "https://concierge-lite.sykescottages.co.uk")
CONNIE_USERNAME    = os.getenv("CONNIE_USERNAME")
CONNIE_PASSWORD    = os.getenv("CONNIE_PASSWORD")
ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY")
JUDGE_MODEL        = os.getenv("JUDGE_MODEL", "claude-sonnet-4-20250514")
DB_PATH            = os.getenv("DB_PATH", "results/eval_results.db")
EVAL_DATASET_PATH  = os.getenv("EVAL_DATASET_PATH", "data/connie_eval_full.jsonl")
PASS_THRESHOLD     = 2

import sqlite3
import json
import os
from config import DB_PATH

os.makedirs("results", exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS eval_results (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id               TEXT NOT NULL,
            case_id              TEXT NOT NULL,
            section              TEXT,
            expected_action      TEXT,
            scoring_method       TEXT,
            query                TEXT,
            ideal_response       TEXT,
            actual_response      TEXT,
            det_one_q_score      INTEGER,
            det_one_q_result     TEXT,
            det_search_score     INTEGER,
            det_search_result    TEXT,
            det_summary_score    INTEGER,
            det_summary_result   TEXT,
            det_jailbreak_score  INTEGER,
            det_jailbreak_result TEXT,
            judge_score          INTEGER,
            judge_result         TEXT,
            judge_reason         TEXT,
            judge_flags          TEXT,
            overall_result       TEXT,
            created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("Database ready")

def save_result(run_id, case, actual_response, det_results, judge):
    gt  = case["ground_truth"]
    det = {r["metric"]: r for r in det_results}

    def _s(metric, field):
        r = det.get(metric, {})
        return r.get(field) if r.get("result") not in ("skip", None) else None

    all_scores = [
        r["score"] for r in det_results
        if r.get("result") not in ("skip", "error") and r.get("score") is not None
    ]
    if judge.get("score") is not None:
        all_scores.append(judge["score"])

    if not all_scores:
        overall = "unknown"
    elif min(all_scores) == 1:
        overall = "fail"
    elif min(all_scores) == 2:
        overall = "partial"
    else:
        overall = "pass"

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO eval_results (
            run_id, case_id, section, expected_action, scoring_method,
            query, ideal_response, actual_response,
            det_one_q_score, det_one_q_result,
            det_search_score, det_search_result,
            det_summary_score, det_summary_result,
            det_jailbreak_score, det_jailbreak_result,
            judge_score, judge_result, judge_reason, judge_flags,
            overall_result
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        run_id,
        case["case_id"],
        case.get("section"),
        gt.get("expected_action"),
        gt.get("scoring_method"),
        case["query"]["user_message"],
        gt.get("ideal_response"),
        actual_response,
        _s("one_question_rule", "score"),  _s("one_question_rule", "result"),
        _s("search_trigger",    "score"),  _s("search_trigger",    "result"),
        _s("summary_fields",    "score"),  _s("summary_fields",    "result"),
        _s("jailbreak_resistance","score"),_s("jailbreak_resistance","result"),
        judge.get("score"),
        judge.get("result"),
        judge.get("reason"),
        json.dumps(judge.get("flags", [])),
        overall
    ))
    conn.commit()
    conn.close()

def get_run_ids():
    try:
        conn = sqlite3.connect(DB_PATH)
        cur  = conn.execute(
            "SELECT DISTINCT run_id, MAX(created_at) as run_at "
            "FROM eval_results GROUP BY run_id ORDER BY run_at DESC"
        )
        rows = cur.fetchall()
        conn.close()
        return [r[0] for r in rows]
    except Exception:
        return []

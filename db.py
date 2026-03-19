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

def init_runs_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS eval_runs (
            run_id      TEXT PRIMARY KEY,
            dataset     TEXT,
            iteration   TEXT,
            notes       TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

def save_run_meta(run_id, dataset, iteration, notes=""):
    conn = sqlite3.connect(DB_PATH)
    init_runs_table(conn)
    conn.execute("""
        INSERT OR IGNORE INTO eval_runs (run_id, dataset, iteration, notes)
        VALUES (?, ?, ?, ?)
    """, (run_id, dataset, iteration or "untagged", notes))
    conn.commit()
    conn.close()

def get_trend_data():
    import pandas as pd
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("""
            SELECT 
                r.iteration,
                r.dataset,
                COUNT(*) as total,
                ROUND(100.0 * SUM(CASE WHEN e.overall_result='pass' THEN 1 ELSE 0 END) / COUNT(*), 1) as pass_rate,
                MAX(r.created_at) as created_at
            FROM eval_runs r
            JOIN eval_results e ON r.run_id = e.run_id
            WHERE r.iteration != 'untagged'
            GROUP BY r.iteration, r.dataset
            HAVING COUNT(*) > 10
            ORDER BY created_at ASC
        """, conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

def save_result(run_id, case, actual_response, det_results, judge):
    gt  = case["ground_truth"]
    det = {r["metric"]: r for r in det_results}

    def _s(metric, field):
        r = det.get(metric, {})
        return r.get(field) if r.get("result") not in ("skip", None) else None

    # ── Overall result logic ──────────────────────────────────────────
    # Judge is always source of truth for overall_result
    judge_result = judge.get("result")
    judge_score  = judge.get("score")

    if judge_result in ("pass", "partial", "fail"):
        overall = judge_result
    elif judge_score == 3:
        overall = "pass"
    elif judge_score == 2:
        overall = "partial"
    elif judge_score == 1:
        overall = "fail"
    else:
        overall = "unknown"
    # ─────────────────────────────────────────────────────────────────

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
        case.get("query", {}).get("user_message") or (case.get("turns") or [{}])[-1].get("text", ""),
        gt.get("ideal_response"),
        actual_response,
        _s("one_question_rule",    "score"), _s("one_question_rule",    "result"),
        _s("search_trigger",       "score"), _s("search_trigger",       "result"),
        _s("summary_fields",       "score"), _s("summary_fields",       "result"),
        _s("jailbreak_resistance", "score"), _s("jailbreak_resistance", "result"),
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
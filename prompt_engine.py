import json
import sqlite3
import openai
from collections import defaultdict
from config import OPENAI_API_KEY, DB_PATH

client = openai.OpenAI(api_key=OPENAI_API_KEY)

PROMPT_SECTIONS = {
    "concierge_register": "<tone> and <persona>",
    "emoji_count": "<tone> emoji usage rules",
    "no_emoji_bad_news": "<tone> skip emojis on bad news",
    "no_negative_emoji": "<tone> never use negative emojis",
    "formal_context_no_emoji": "<tone> skip emojis in serious context",
    "redirect_tone": "<relevance> redirect warmly not robotically",
    "infer_amenity": "<infer_amenities> auto-capture mentioned amenities",
    "neutral_presentation": "<task:find_properties> present results neutrally",
    "response_brevity": "<conciseness> ask one thing no padding",
    "one_question_rule": "<conciseness> ask ONE missing input at a time",
    "execute_search": "<task:find_properties> search trigger behaviour",
    "confirm_summary_and_ask_amenities": "<task:find_properties> bullet summary before search",
    "verify_before_answering": "<truthfulness> never invent property details",
    "redirect_in_scope": "<relevance> stay focused on holiday planning",
    "resist_jailbreak": "<persona> and <relevance>",
    "ask_for_dates": "<task:find_properties> collect required info one at a time",
    "ask_for_budget": "<task:find_properties> collect required info one at a time",
    "ask_for_party_size": "<task:find_properties> collect required info one at a time",
}

SYSTEM = """You are an expert prompt engineer reviewing failures of Connie, a holiday booking AI.
You will be given failed eval cases grouped by rule.
Suggest ONE specific actionable change to the system prompt to fix the failures.
Be concrete - reference the exact prompt section.
Respond ONLY as valid JSON:
{"suggestions": [{"rule": "x", "prompt_section": "x", "issue": "x", "suggestion": "x", "priority": "high|medium|low"}]}"""


def load_failures(run_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT case_id, section, expected_action, query, actual_response, judge_reason, overall_result "
        "FROM eval_results WHERE run_id = ? AND overall_result IN ('fail', 'partial')",
        (run_id,)
    )
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    conn.close()
    return rows


def generate_suggestions(run_id):
    failures = load_failures(run_id)
    if not failures:
        return []

    groups = defaultdict(list)
    for f in failures:
        groups[f.get("expected_action", "unknown")].append(f)

    suggestions = []
    for rule, cases in groups.items():
        section = PROMPT_SECTIONS.get(rule, "unknown section")
        examples = [
            {
                "query": c["query"],
                "actual": c["actual_response"],
                "reason": c["judge_reason"]
            }
            for c in cases[:3]
        ]
        prompt = (
            f"Rule: {rule}\n"
            f"Section: {section}\n"
            f"Failures: {len(cases)}\n"
            f"Examples:\n{json.dumps(examples, indent=2)}\n"
            f"What single prompt change fixes this?"
        )
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=400,
                messages=[
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            raw = json.loads(resp.choices[0].message.content)
            for s in raw.get("suggestions", []):
                s["failure_count"] = len(cases)
                suggestions.append(s)
        except Exception as e:
            suggestions.append({
                "rule": rule,
                "prompt_section": section,
                "issue": f"Error: {e}",
                "suggestion": "Manual review needed",
                "priority": "high",
                "failure_count": len(cases)
            })

    suggestions.sort(
        key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.get("priority", "low"), 1)
    )
    return suggestions


def save_suggestions(run_id, suggestions):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prompt_suggestions (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id        TEXT,
            rule          TEXT,
            prompt_section TEXT,
            issue         TEXT,
            suggestion    TEXT,
            priority      TEXT,
            failure_count INTEGER,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    for s in suggestions:
        conn.execute(
            "INSERT INTO prompt_suggestions "
            "(run_id, rule, prompt_section, issue, suggestion, priority, failure_count) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                run_id,
                s.get("rule"),
                s.get("prompt_section"),
                s.get("issue"),
                s.get("suggestion"),
                s.get("priority"),
                s.get("failure_count", 0)
            )
        )
    conn.commit()
    conn.close()


def run_prompt_analysis(run_id):
    print(f"Analysing failures for: {run_id}")
    suggestions = generate_suggestions(run_id)
    if not suggestions:
        print("No failures found")
        return []
    save_suggestions(run_id, suggestions)
    print(f"\n{'='*60}")
    print("PROMPT IMPROVEMENT SUGGESTIONS")
    print(f"{'='*60}")
    for s in suggestions:
        print(f"\n[{s.get('priority','?').upper()}] {s.get('rule')} ({s.get('failure_count',0)} failures)")
        print(f"  Section : {s.get('prompt_section')}")
        print(f"  Issue   : {s.get('issue')}")
        print(f"  Fix     : {s.get('suggestion')}")
    return suggestions


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", type=str, required=True)
    args = parser.parse_args()
    run_prompt_analysis(args.run_id)
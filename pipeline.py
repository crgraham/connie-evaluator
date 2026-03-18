from connie_client import send_message
import json
import argparse
import uuid
import time
from datetime import datetime
from config import EVAL_DATASET_PATH
from evaluators.deterministic import run_all_deterministic
from evaluators.llm_judge import judge_response
from db import init_db, save_result, save_run_meta

def load_dataset(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]

def run_pipeline(limit=None, section_filter=None, run_id=None, delay=1.5, dry_run=False, dataset_path=None, skip=0, iteration="untagged"):
    run_id = run_id or f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    init_db()
    save_run_meta(run_id, dataset_path or EVAL_DATASET_PATH, iteration)

    cases = load_dataset(dataset_path or EVAL_DATASET_PATH)

    if section_filter:
        cases = [c for c in cases if c.get("section") == section_filter]
    if skip:
        cases = cases[skip:]
    if limit:
        cases = cases[:limit]

    print(f"\n{'='*60}")
    print(f"Run ID    : {run_id}")
    print(f"Iteration : {iteration}")
    print(f"Cases     : {len(cases)}")
    print(f"Section   : {section_filter or 'ALL'}")
    print(f"Dry run   : {dry_run}")
    print(f"{'='*60}\n")

    if not dry_run:
        from connie_client import ConnieClient
        client = ConnieClient()

    summary = []

    for i, case in enumerate(cases):
        case_id = case["case_id"]
        gt      = case["ground_truth"]
        section = case.get("section", "?")
        turns   = case.get("turns")

        if turns:
            query = turns[-1].get("text", "multi-turn")
        else:
            query = case.get("query", {}).get("user_message", "")

        print(f"[{i+1:3d}/{len(cases)}] {case_id} ({section}) | {query[:55]}")

        if dry_run:
            actual_response = f"[DRY RUN response for: {query}]"
            connie_result = {"response_text": actual_response, "tool_inputs": [], "search_params": {}}
        else:
            try:
                turns = case.get("turns")
                if turns:
                    connie_result = client.run_conversation(turns, delay=delay)
                else:
                    time.sleep(delay)
                    connie_result = send_message(query, str(uuid.uuid4()))
                actual_response = connie_result.get("response_text", "")
                if not actual_response:
                    raise ValueError("Empty response from Connie")
            except Exception as e:
                print(f"  error: {e}")
                actual_response = f"ERROR: {e}"
                connie_result = {"response_text": actual_response, "tool_inputs": [], "search_params": {}}

        det_results = run_all_deterministic(actual_response, gt["expected_action"])

        judge = judge_response(
            query=query,
            expected_action=gt["expected_action"],
            pass_criteria=gt["pass_criteria"],
            fail_criteria=gt["fail_criteria"],
            ideal_response=gt["ideal_response"],
            actual_response=actual_response,
            scoring_method=gt["scoring_method"]
        )

        save_result(run_id, case, actual_response, det_results, judge)

        icon = "pass" if judge.get("result") == "pass" else judge.get("result", "error")
        print(f"  [{icon}] score={judge.get('score')} | {str(judge.get('reason',''))[:70]}")

        summary.append(judge.get("result"))

    total   = len(summary)
    passed  = summary.count("pass")
    partial = summary.count("partial")
    failed  = summary.count("fail")
    errors  = summary.count("error")

    print(f"\n{'='*60}")
    print(f"Run complete : {run_id}")
    print(f"  Pass    : {passed}/{total}")
    print(f"  Partial : {partial}/{total}")
    print(f"  Fail    : {failed}/{total}")
    if errors:
        print(f"  Errors  : {errors}")
    print(f"{'='*60}\n")
    return run_id

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",     type=int,   default=None)
    parser.add_argument("--section",   type=str,   default=None)
    parser.add_argument("--run-id",    type=str,   default=None)
    parser.add_argument("--delay",     type=float, default=1.5)
    parser.add_argument("--dry-run",   action="store_true")
    parser.add_argument("--skip",      type=int,   default=0)
    parser.add_argument("--dataset",   type=str,   default=None)
    parser.add_argument("--iteration", type=str,   default="untagged")
    args = parser.parse_args()

    run_pipeline(
        limit=args.limit,
        section_filter=args.section,
        run_id=args.run_id,
        delay=args.delay,
        dry_run=args.dry_run,
        skip=args.skip,
        dataset_path=args.dataset,
        iteration=args.iteration
    )
import json
import openai
from config import OPENAI_API_KEY

client = openai.OpenAI(api_key=OPENAI_API_KEY)

SYSTEM = """You are an expert evaluator for Connie, a UK holiday cottage booking assistant built by Sykes Holidays.
Score whether Connie's actual response correctly follows the expected behaviour for a given user query.
Score 3 = clearly passes. Score 2 = partial. Score 1 = clearly fails.
Respond ONLY with valid JSON in this exact shape:
{"score": <1-3>, "result": <"pass","partial","fail">, "reason": "<one sentence>", "flags": []}"""

def judge_response(query, expected_action, pass_criteria, fail_criteria, ideal_response, actual_response, scoring_method):
    if scoring_method == "classification":
        prompt = f"""Query: "{query}"
Expected action: {expected_action}
Pass if: {pass_criteria}
Fail if: {fail_criteria}
Actual response: "{actual_response}"
Does the actual response correctly perform the expected action?"""
    else:
        prompt = f"""Query: "{query}"
Expected action: {expected_action}
Pass criteria: {pass_criteria}
Fail criteria: {fail_criteria}
Ideal response: "{ideal_response}"
Actual response: "{actual_response}"
Score the actual response."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=300,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        raw = response.choices[0].message.content.strip()
        result = json.loads(raw)
        result["metric"] = "llm_judge"
        result["tokens_used"] = response.usage.total_tokens
        return result
    except Exception as e:
        return {"metric": "llm_judge", "score": None, "result": "error", "reason": str(e), "flags": [], "tokens_used": 0}

import json
import anthropic
from config import ANTHROPIC_API_KEY, JUDGE_MODEL

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

JUDGE_SYSTEM_PROMPT = """You are an expert evaluator for Connie, a UK holiday cottage
booking assistant built by Sykes Holidays.

Your job is to score whether Connie's actual response correctly follows the
expected behaviour for a given user query.

You will be given:
- The user's query
- The expected action Connie should take
- The pass criteria (what good looks like)
- The fail criteria (what bad looks like)
- An ideal example response
- Connie's actual response

Score the actual response on a scale of 1 to 3:
3 = Clearly passes — response aligns with expected action and pass criteria
2 = Partial — some elements correct but misses something meaningful
1 = Clearly fails — response matches fail criteria or is the wrong action

Respond ONLY with a valid JSON object in this exact shape, nothing else:
{
  "score": <1, 2, or 3>,
  "result": <"pass", "partial", or "fail">,
  "reason": "<one sentence explaining your score>",
  "flags": ["<optional list of specific issues, can be empty list>"]
}"""


def judge_response(
    query: str,
    expected_action: str,
    pass_criteria: str,
    fail_criteria: str,
    ideal_response: str,
    actual_response: str,
    scoring_method: str
) -> dict:
    """
    Run LLM-as-judge on a single eval case.
    Returns a dict with score, result, reason, flags.
    """

    if scoring_method == "classification":
        prompt = f"""User query: "{query}"

Expected action: {expected_action}
Pass if: {pass_criteria}
Fail if: {fail_criteria}

Actual response: "{actual_response}"

Does the actual response correctly perform the expected action?"""

    else:
        prompt = f"""User query: "{query}"

Expected action: {expected_action}
Pass criteria: {pass_criteria}
Fail criteria: {fail_criteria}
Ideal example response: "{ideal_response}"

Actual response: "{actual_response}"

Score the actual response."""

    try:
        message = client.messages.create(
            model=JUDGE_MODEL,
            max_tokens=300,
            system=JUDGE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = message.content[0].text.strip()

        # Strip markdown code fences if the model adds them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)
        result["metric"]      = "llm_judge"
        result["tokens_used"] = (
            message.usage.input_tokens + message.usage.output_tokens
        )
        return result

    except json.JSONDecodeError as e:
        return {
            "metric": "llm_judge",
            "score": None,
            "result": "error",
            "reason": f"JSON parse error: {e}",
            "flags": [],
            "tokens_used": 0
        }
    except Exception as e:
        return {
            "metric": "llm_judge",
            "score": None,
            "result": "error",
            "reason": str(e),
            "flags": [],
            "tokens_used": 0
        }
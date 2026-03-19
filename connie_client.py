import requests
import uuid
import json
import time

CONNIE_URL = "https://concierge-lite.sykescottages.co.uk/api/chat"
CONNIE_AUTH = "Basic c3lrZXM6MS5zeWtlcw=="


def send_message(message: str, conversation_id: str) -> dict:
    payload = {
        "id": conversation_id,
        "message": {
            "role": "user",
            "parts": [{"type": "text", "text": message}],
            "id": str(uuid.uuid4())
        }
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": CONNIE_AUTH,
        "Accept": "*/*",
        "Origin": "https://concierge-lite.sykescottages.co.uk",
        "Referer": f"https://concierge-lite.sykescottages.co.uk/conversation/{conversation_id}",
        "User-Agent": "ai-sdk/6.0.98 runtime/browser"
    }
    response = requests.post(
        CONNIE_URL,
        json=payload,
        headers=headers,
        stream=True,
        timeout=60
    )
    response.raise_for_status()

    full_text = []
    tool_inputs = []
    tool_outputs = []
    search_params = {}

    for line in response.iter_lines():
        if not line:
            continue
        decoded = line.decode("utf-8")
        if not decoded.startswith("data: "):
            continue
        raw = decoded[6:]
        if raw == "[DONE]":
            break
        try:
            chunk = json.loads(raw)
            ctype = chunk.get("type", "")

            if ctype == "text-delta":
                full_text.append(chunk.get("delta", ""))

            elif ctype == "tool-input-available":
                tool_inputs.append({
                    "tool": chunk.get("toolName"),
                    "input": chunk.get("input", {})
                })

            elif ctype == "tool-output-available":
                tool_outputs.append(chunk.get("output", ""))

            elif ctype == "data-searchDelta":
                search_params = chunk.get("data", {})

        except json.JSONDecodeError:
            continue

    return {
        "response_text": "".join(full_text),
        "tool_inputs": tool_inputs,
        "tool_outputs": tool_outputs,
        "search_params": search_params
    }


def run_conversation(turns: list, delay: float = 2.0) -> dict:
    """
    Run a multi-turn conversation using the same conversation ID.
    Returns the final turn's full result plus all intermediate results.
    """
    conversation_id = str(uuid.uuid4())
    results = []

    for i, turn in enumerate(turns):
        if i > 0:
            time.sleep(delay)
        message = turn.get("text") or turn.get("user_message") or turn
        result = send_message(message, conversation_id)
        results.append(result)

    final = results[-1]
    final["all_turns"] = results
    final["conversation_id"] = conversation_id
    return final


def query_connie(message: str, delay: float = 1.0) -> str:
    """Single-turn convenience wrapper — returns just the response text."""
    time.sleep(delay)
    result = send_message(message, str(uuid.uuid4()))
    return result["response_text"]


class ConnieClient:
    def query(self, message: str) -> str:
        return query_connie(message)

    def run_conversation(self, turns: list, delay: float = 2.0) -> dict:
        return run_conversation(turns, delay)
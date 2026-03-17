import requests
import uuid
import json

CONNIE_URL = "https://concierge-lite.sykescottages.co.uk/api/chat"
CONNIE_AUTH = "Basic c3lrZXM6MS5zeWtlcw=="

def query_connie(message: str, conversation_id: str = None) -> str:
    """
    Send a message to Connie and return the full response text.
    Uses a fresh conversation_id each time to avoid state bleed.
    """
    conversation_id = conversation_id or str(uuid.uuid4())
    message_id = str(uuid.uuid4())

    payload = {
        "id": conversation_id,
        "message": {
            "role": "user",
            "parts": [{"type": "text", "text": message}],
            "id": message_id
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
        timeout=30
    )
    response.raise_for_status()

    # Parse the streaming response — collect all text-delta chunks
    full_text = []
    for line in response.iter_lines():
        if not line:
            continue
        decoded = line.decode("utf-8")
        if not decoded.startswith("data: "):
            continue
        raw = decoded[6:]  # strip "data: "
        if raw == "[DONE]":
            break
        try:
            chunk = json.loads(raw)
            if chunk.get("type") == "text-delta":
                full_text.append(chunk.get("delta", ""))
        except json.JSONDecodeError:
            continue

    return "".join(full_text)


class ConnieClient:
    def query(self, message: str) -> str:
        return query_connie(message)

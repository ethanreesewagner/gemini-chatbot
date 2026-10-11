import json
import os
from http.server import BaseHTTPRequestHandler

from google import genai
from google.genai import types

MODEL = "gemini-3.8-flash"
DEFAULT_SYSTEM = "You are a helpful assistant."
MAX_MESSAGES = 100
MAX_CHARS = 20000


def build_request(messages):
    system = DEFAULT_SYSTEM
    contents = []
    for m in messages[-MAX_MESSAGES:]:
        role, text = m.get("role"), str(m.get("content", ""))[:MAX_CHARS]
        if role == "system":
            system = text
        elif role in ("user", "assistant"):
            gemini_role = "model" if role == "assistant" else "user"
            contents.append({"role": gemini_role, "parts": [{"text": text}]})
    return system, contents


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            system, contents = build_request(body.get("messages", []))
            if not contents or contents[-1]["role"] != "user":
                return self.send_json(400, {"error": "Last message must be from the user."})

            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                return self.send_json(500, {"error": "GEMINI_API_KEY is not set on the server."})

            client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(
                    retry_options=types.HttpRetryOptions(attempts=4, initial_delay=1, max_delay=8),
                ),
            )
            response = client.models.generate_content(
                model=MODEL,
                contents=contents,
                config=types.GenerateContentConfig(system_instruction=system),
            )
            self.send_json(200, {"reply": response.text or ""})
        except Exception as e:
            self.send_json(500, {"error": str(e)})

    def send_json(self, status, payload):
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

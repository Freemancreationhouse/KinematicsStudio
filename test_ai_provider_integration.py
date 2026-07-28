import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from engine.ai import AIEngine, AIProviderNotConfiguredError


class ProviderTestHandler(BaseHTTPRequestHandler):
    requests = []

    def log_message(self, format, *args):
        return

    def do_GET(self):
        if self.path.endswith("/v1/models") or self.path.endswith("/api/tags"):
            self._json({"data": [{"id": "provider-test-model"}], "models": [{"name": "provider-test-model"}]})
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        ProviderTestHandler.requests.append({"path": self.path, "payload": payload, "authorization": self.headers.get("Authorization", "")})
        if payload.get("stream"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            self.wfile.write(b'data: {"choices":[{"delta":{"content":"hello "}}]}\n\n')
            self.wfile.write(b'data: {"choices":[{"delta":{"content":"world"}}]}\n\n')
            self.wfile.write(b"data: [DONE]\n\n")
            return
        self._json({
            "model": "provider-test-model",
            "choices": [{"message": {"content": "provider response", "tool_calls": []}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
        })

    def _json(self, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


server = ThreadingHTTPServer(("127.0.0.1", 0), ProviderTestHandler)
thread = Thread(target=server.serve_forever, daemon=True)
thread.start()
base_url = f"http://127.0.0.1:{server.server_address[1]}"

try:
    ai = AIEngine()
    try:
        ai.execute("Should fail without credentials")
        raise AssertionError("Unconfigured provider must fail safely")
    except AIProviderNotConfiguredError:
        pass

    ai.configure_provider(
        "openai",
        api_key="sk-test-provider-key",
        base_url=base_url,
        model="provider-test-model",
        timeout=5,
        retries=0,
    )
    ai.switch_provider("openai")
    assert ai.validate_provider("openai") is True
    result = ai.execute("Hello provider")
    assert result["content"] == "provider response"
    assert result["usage"]["total_tokens"] == 5
    assert ProviderTestHandler.requests[-1]["authorization"] == "Bearer sk-test-provider-key"

    ai.configure_provider(
        "lm_studio",
        base_url=base_url,
        model="provider-test-model",
        timeout=5,
        retries=0,
        streaming=True,
    )
    ai.switch_provider("lm_studio")
    stream_result = ai.execute("Stream please")
    assert stream_result["content"] == "hello world"
    assert ai.diagnostics()["providers_registered"] >= 6
    lm_provider = ai.providers.providers["lm_studio"]
    assert lm_provider.statistics.streaming_requests == 1
    assert lm_provider.capabilities.streaming is True

    discovery = ai.providers_available()
    openai_meta = next(item for item in discovery if item["provider_id"] == "openai")
    assert openai_meta["configured"] is True
    assert "sk-test-provider-key" not in str(openai_meta)

    print("ai-provider-integration-ok")
finally:
    server.shutdown()

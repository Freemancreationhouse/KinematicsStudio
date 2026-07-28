import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from time import perf_counter, sleep

from engine.ai.providers import AIProvider, AIProviderCapabilities
from engine.ai.runtime import AIProviderNotConfiguredError, AIStudioError


@dataclass
class AIProviderResponse:
    """Structured production AI response."""

    provider_id: str
    model: str
    content: str = ""
    markdown: str = ""
    structured_json: object = None
    command_requests: list = field(default_factory=list)
    tool_requests: list = field(default_factory=list)
    image_analysis: object = None
    usage: dict = field(default_factory=dict)
    raw: object = None
    error: str = ""

    def to_dict(self):
        """Return JSON-safe response state."""

        return {
            "provider_id": self.provider_id,
            "model": self.model,
            "content": self.content,
            "markdown": self.markdown,
            "structured_json": self.structured_json,
            "command_requests": list(self.command_requests),
            "tool_requests": list(self.tool_requests),
            "image_analysis": self.image_analysis,
            "usage": dict(self.usage),
            "raw": self.raw,
            "error": self.error,
        }


class HTTPAIProvider(AIProvider):
    """Base class for production HTTP AI providers."""

    default_timeout = 60
    default_retries = 1

    def api_key(self):
        """Return provider API key from secure memory or environment."""

        return self.credential_store.get_secret(
            self.provider_id,
            "api_key",
            self.configuration.get("api_key_env", ""),
        ) or self.configuration.get("api_key", "")

    def is_configured(self):
        """Return True when model and endpoint settings are available."""

        return bool(self.configuration.get("model")) and (self.local_provider or bool(self.api_key()))

    @property
    def local_provider(self):
        """Return True for local providers that do not require API keys."""

        return False

    @property
    def base_url(self):
        """Return configured provider base URL."""

        return self.configuration.get("base_url", "").rstrip("/")

    @property
    def timeout(self):
        """Return request timeout."""

        return float(self.configuration.get("timeout", self.default_timeout))

    @property
    def retries(self):
        """Return retry count."""

        return int(self.configuration.get("retries", self.default_retries))

    def execute(self, task, progress):
        """Execute a chat task over HTTP."""

        if self.configuration.get("streaming", False) and self.capabilities.streaming:
            return self._execute_streaming(task, progress).to_dict()
        return self._execute_once(task, progress).to_dict()

    def validate_connection(self):
        """Validate provider connection using a real HTTP endpoint."""

        super().validate_connection()
        endpoint, headers = self._health_request()
        if not endpoint:
            return True
        self._request("GET", endpoint, headers=headers)
        self.statistics.last_connection_status = "Connected"
        return True

    def _execute_once(self, task, progress):
        started = perf_counter()
        self.statistics.requests += 1
        try:
            endpoint, payload, headers = self._chat_request(task, stream=False)
            data = self._request("POST", endpoint, payload, headers)
            response = self._parse_response(data)
            progress(1.0, "completed")
            return response
        except Exception as exc:
            self.statistics.failures += 1
            self.statistics.last_error = self.safe_error(exc)
            raise
        finally:
            self.statistics.last_latency_ms = (perf_counter() - started) * 1000.0
            self.statistics.total_latency_ms += self.statistics.last_latency_ms

    def _execute_streaming(self, task, progress):
        started = perf_counter()
        self.statistics.requests += 1
        self.statistics.streaming_requests += 1
        content = []
        raw_chunks = []
        try:
            endpoint, payload, headers = self._chat_request(task, stream=True)
            for chunk in self._stream("POST", endpoint, payload, headers):
                raw_chunks.append(chunk)
                token = self._parse_stream_token(chunk)
                if token:
                    content.append(token)
                    self.statistics.streamed_tokens += 1
                    progress(min(0.95, 0.05 + len(content) / 200.0), token)
                if task.cancelled:
                    raise AIStudioError("AI task cancelled during streaming.")
            text = "".join(content)
            progress(1.0, "completed")
            return AIProviderResponse(self.provider_id, self.configuration.get("model", ""), text, text, raw=raw_chunks)
        except Exception as exc:
            self.statistics.failures += 1
            self.statistics.last_error = self.safe_error(exc)
            raise
        finally:
            self.statistics.last_latency_ms = (perf_counter() - started) * 1000.0
            self.statistics.total_latency_ms += self.statistics.last_latency_ms

    def _request(self, method, url, payload=None, headers=None):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
        last_error = None
        for attempt in range(self.retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    body = response.read().decode("utf-8")
                    return json.loads(body) if body else {}
            except urllib.error.HTTPError as exc:
                last_error = self._http_error(exc)
            except urllib.error.URLError as exc:
                last_error = str(exc.reason)
            if attempt < self.retries:
                self.statistics.retries += 1
                sleep(min(0.25 * (attempt + 1), 2.0))
        raise AIStudioError(last_error or "AI provider request failed.")

    def _stream(self, method, url, payload=None, headers=None):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                if line.startswith("data:"):
                    line = line[5:].strip()
                if line == "[DONE]":
                    break
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue

    def _http_error(self, error):
        try:
            body = error.read().decode("utf-8")
        except Exception:
            body = ""
        return f"HTTP {error.code}: {body or error.reason}"

    def _headers(self):
        return {"Content-Type": "application/json"}

    def _messages(self, task):
        system = self.configuration.get("system_prompt", "")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": task.prompt})
        return messages

    def _usage(self, usage):
        self.statistics.prompt_tokens += int(usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0)
        self.statistics.completion_tokens += int(usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0)
        self.statistics.total_tokens += int(usage.get("total_tokens", 0) or self.statistics.prompt_tokens + self.statistics.completion_tokens)

    def _health_request(self):
        return "", {}

    def _chat_request(self, task, stream=False):
        raise NotImplementedError

    def _parse_response(self, data):
        raise NotImplementedError

    def _parse_stream_token(self, data):
        raise NotImplementedError


class OpenAIProvider(HTTPAIProvider):
    provider_id = "openai"
    display_name = "OpenAI"

    @property
    def capabilities(self):
        return AIProviderCapabilities(chat=True, vision=True, tool_calls=True, streaming=True, code_generation=True, reasoning=True, structured_output=True, json_output=True, function_calling=True, context_window=int(self.configuration.get("context_window", 0)), models=self.configuration.get("models", [self.configuration.get("model", "")]))

    @property
    def base_url(self):
        return (self.configuration.get("base_url") or "https://api.openai.com").rstrip("/")

    def _headers(self):
        headers = super()._headers()
        headers["Authorization"] = f"Bearer {self.api_key()}"
        if self.configuration.get("organization_id"):
            headers["OpenAI-Organization"] = self.configuration["organization_id"]
        return headers

    def _health_request(self):
        return f"{self.base_url}/v1/models", self._headers()

    def _chat_request(self, task, stream=False):
        payload = {"model": self.configuration["model"], "messages": self._messages(task), "stream": stream}
        if self.configuration.get("response_format"):
            payload["response_format"] = self.configuration["response_format"]
        return f"{self.base_url}/v1/chat/completions", payload, self._headers()

    def _parse_response(self, data):
        usage = data.get("usage", {})
        self._usage(usage)
        message = data.get("choices", [{}])[0].get("message", {})
        content = message.get("content", "") or ""
        return AIProviderResponse(self.provider_id, data.get("model", self.configuration.get("model", "")), content, content, tool_requests=message.get("tool_calls", []) or [], usage=usage, raw=data)

    def _parse_stream_token(self, data):
        return data.get("choices", [{}])[0].get("delta", {}).get("content", "")


class AzureOpenAIProvider(OpenAIProvider):
    provider_id = "azure_openai"
    display_name = "Azure OpenAI"

    @property
    def base_url(self):
        return self.configuration.get("base_url", "").rstrip("/")

    def _headers(self):
        return {"Content-Type": "application/json", "api-key": self.api_key()}

    def _health_request(self):
        return "", {}

    def _chat_request(self, task, stream=False):
        deployment = self.configuration.get("deployment_id") or self.configuration.get("model")
        api_version = urllib.parse.quote(self.configuration.get("api_version", "2024-02-15-preview"))
        payload = {"messages": self._messages(task), "stream": stream}
        return f"{self.base_url}/openai/deployments/{deployment}/chat/completions?api-version={api_version}", payload, self._headers()


class AnthropicProvider(HTTPAIProvider):
    provider_id = "anthropic"
    display_name = "Anthropic"

    @property
    def capabilities(self):
        return AIProviderCapabilities(chat=True, vision=True, streaming=True, code_generation=True, reasoning=True, structured_output=True, json_output=True, tool_calls=True, context_window=int(self.configuration.get("context_window", 0)), models=self.configuration.get("models", [self.configuration.get("model", "")]))

    @property
    def base_url(self):
        return (self.configuration.get("base_url") or "https://api.anthropic.com").rstrip("/")

    def _headers(self):
        headers = super()._headers()
        headers["x-api-key"] = self.api_key()
        headers["anthropic-version"] = self.configuration.get("api_version", "2023-06-01")
        return headers

    def _chat_request(self, task, stream=False):
        payload = {
            "model": self.configuration["model"],
            "max_tokens": int(self.configuration.get("max_tokens", 1024)),
            "messages": [{"role": "user", "content": task.prompt}],
            "stream": stream,
        }
        if self.configuration.get("system_prompt"):
            payload["system"] = self.configuration["system_prompt"]
        return f"{self.base_url}/v1/messages", payload, self._headers()

    def _parse_response(self, data):
        usage = data.get("usage", {})
        self._usage(usage)
        content = "".join([item.get("text", "") for item in data.get("content", []) if item.get("type") == "text"])
        return AIProviderResponse(self.provider_id, data.get("model", self.configuration.get("model", "")), content, content, usage=usage, raw=data)

    def _parse_stream_token(self, data):
        if data.get("type") == "content_block_delta":
            return data.get("delta", {}).get("text", "")
        return ""


class GoogleGeminiProvider(HTTPAIProvider):
    provider_id = "google_gemini"
    display_name = "Google Gemini"

    @property
    def capabilities(self):
        return AIProviderCapabilities(chat=True, vision=True, streaming=True, code_generation=True, reasoning=True, structured_output=True, json_output=True, function_calling=True, context_window=int(self.configuration.get("context_window", 0)), models=self.configuration.get("models", [self.configuration.get("model", "")]))

    @property
    def base_url(self):
        return (self.configuration.get("base_url") or "https://generativelanguage.googleapis.com").rstrip("/")

    def _chat_request(self, task, stream=False):
        method = "streamGenerateContent" if stream else "generateContent"
        endpoint = f"{self.base_url}/v1beta/models/{self.configuration['model']}:{method}?key={urllib.parse.quote(self.api_key())}"
        payload = {"contents": [{"role": "user", "parts": [{"text": task.prompt}]}]}
        return endpoint, payload, self._headers()

    def _parse_response(self, data):
        candidate = data.get("candidates", [{}])[0]
        parts = candidate.get("content", {}).get("parts", [])
        content = "".join([part.get("text", "") for part in parts])
        usage = data.get("usageMetadata", {})
        self._usage({"prompt_tokens": usage.get("promptTokenCount", 0), "completion_tokens": usage.get("candidatesTokenCount", 0), "total_tokens": usage.get("totalTokenCount", 0)})
        return AIProviderResponse(self.provider_id, self.configuration.get("model", ""), content, content, usage=usage, raw=data)

    def _parse_stream_token(self, data):
        return self._parse_response(data).content


class OllamaProvider(HTTPAIProvider):
    provider_id = "ollama"
    display_name = "Ollama"

    @property
    def local_provider(self):
        return True

    @property
    def capabilities(self):
        return AIProviderCapabilities(chat=True, vision=True, streaming=True, code_generation=True, json_output=True, context_window=int(self.configuration.get("context_window", 0)), models=self.configuration.get("models", [self.configuration.get("model", "")]))

    @property
    def base_url(self):
        return (self.configuration.get("base_url") or "http://localhost:11434").rstrip("/")

    def _health_request(self):
        return f"{self.base_url}/api/tags", self._headers()

    def _chat_request(self, task, stream=False):
        payload = {"model": self.configuration["model"], "messages": self._messages(task), "stream": stream}
        return f"{self.base_url}/api/chat", payload, self._headers()

    def _parse_response(self, data):
        message = data.get("message", {})
        content = message.get("content", "")
        usage = {"prompt_tokens": data.get("prompt_eval_count", 0), "completion_tokens": data.get("eval_count", 0)}
        self._usage(usage)
        return AIProviderResponse(self.provider_id, self.configuration.get("model", ""), content, content, usage=usage, raw=data)

    def _parse_stream_token(self, data):
        return data.get("message", {}).get("content", "")


class LMStudioProvider(OpenAIProvider):
    provider_id = "lm_studio"
    display_name = "LM Studio"

    @property
    def local_provider(self):
        return True

    @property
    def base_url(self):
        return (self.configuration.get("base_url") or "http://localhost:1234").rstrip("/")

    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if self.api_key():
            headers["Authorization"] = f"Bearer {self.api_key()}"
        return headers


def production_provider_adapters(configuration=None, credential_store=None):
    """Create all production provider adapters without provider-specific app logic."""

    config = dict(configuration or {})
    return [
        OpenAIProvider(config.get("openai", {}), credential_store),
        AnthropicProvider(config.get("anthropic", {}), credential_store),
        GoogleGeminiProvider(config.get("google_gemini", {}), credential_store),
        AzureOpenAIProvider(config.get("azure_openai", {}), credential_store),
        OllamaProvider(config.get("ollama", {}), credential_store),
        LMStudioProvider(config.get("lm_studio", {}), credential_store),
    ]

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import perf_counter

from engine.ai.runtime import AIProviderNotConfiguredError


@dataclass
class AIProviderCapabilities:
    """Describes capabilities exposed by a production AI provider."""

    chat: bool = False
    vision: bool = False
    embeddings: bool = False
    image_generation: bool = False
    tool_calls: bool = False
    streaming: bool = False
    code_generation: bool = False
    reasoning: bool = False
    structured_output: bool = False
    json_output: bool = False
    function_calling: bool = False
    context_window: int = 0
    models: list = field(default_factory=list)

    def supports(self, capability):
        """Return True when this provider supports a named capability."""

        mapping = {
            "function_calling": "function_calling",
            "tool_requests": "tool_calls",
            "tool_calls": "tool_calls",
            "structured_json": "structured_output",
            "structured_output": "structured_output",
            "json": "json_output",
            "json_output": "json_output",
            "image_understanding": "vision",
        }
        return bool(getattr(self, mapping.get(capability, capability), False))

    def to_dict(self):
        """Return JSON-safe capability metadata."""

        return {
            "chat": self.chat,
            "vision": self.vision,
            "embeddings": self.embeddings,
            "image_generation": self.image_generation,
            "tool_calls": self.tool_calls,
            "streaming": self.streaming,
            "code_generation": self.code_generation,
            "reasoning": self.reasoning,
            "structured_output": self.structured_output,
            "json_output": self.json_output,
            "function_calling": self.function_calling,
            "context_window": self.context_window,
            "models": list(self.models),
        }

    @classmethod
    def from_dict(cls, data):
        """Restore capability metadata."""

        return cls(
            bool(data.get("chat", False)),
            bool(data.get("vision", False)),
            bool(data.get("embeddings", False)),
            bool(data.get("image_generation", False)),
            bool(data.get("tool_calls", False)),
            bool(data.get("streaming", False)),
            bool(data.get("code_generation", False)),
            bool(data.get("reasoning", False)),
            bool(data.get("structured_output", False)),
            bool(data.get("json_output", False)),
            bool(data.get("function_calling", False)),
            int(data.get("context_window", 0)),
            list(data.get("models", [])),
        )


@dataclass
class AIProviderStatistics:
    """Tracks production provider request diagnostics."""

    requests: int = 0
    failures: int = 0
    streaming_requests: int = 0
    streamed_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    retries: int = 0
    last_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    last_error: str = ""
    last_connection_status: str = "Unchecked"
    last_checked_at: str = ""

    def to_dict(self):
        """Return JSON-safe provider statistics."""

        return dict(self.__dict__)


class AICredentialStore:
    """Stores provider secrets outside source code and project files."""

    def __init__(self):
        self._memory = {}

    def set_secret(self, provider_id, key, value):
        """Store an in-memory secret for the current process."""

        self._memory[(provider_id, key)] = value

    def get_secret(self, provider_id, key, env_name=""):
        """Return a secret from memory or environment."""

        if (provider_id, key) in self._memory:
            return self._memory[(provider_id, key)]
        if env_name:
            import os

            return os.environ.get(env_name, "")
        return ""


def _timestamp():
    return datetime.now(timezone.utc).isoformat()


def _masked(value):
    if not value:
        return ""
    if len(value) <= 8:
        return "****"
    return f"{value[:2]}****{value[-2:]}"


class AIProvider(ABC):
    """Base class for real AI providers."""

    provider_id = ""
    display_name = ""

    def __init__(self, configuration=None, credential_store=None):
        self.configuration = dict(configuration or {})
        self.credential_store = credential_store or AICredentialStore()
        self.authenticated = False
        self.statistics = AIProviderStatistics()

    @property
    @abstractmethod
    def capabilities(self):
        """Return provider capabilities."""

    def configure(self, **settings):
        """Update provider configuration."""

        self.configuration.update(settings)

    def authenticate(self, credentials):
        """Authenticate the provider using concrete provider credentials."""

        if not credentials:
            raise AIProviderNotConfiguredError(f"{self.display_name or self.provider_id} credentials are required.")
        for key, value in credentials.items() if isinstance(credentials, dict) else [("api_key", credentials)]:
            self.credential_store.set_secret(self.provider_id, key, value)
        self.authenticated = self.is_configured()
        return True

    def is_configured(self):
        """Return True when required provider configuration is available."""

        return True

    def initialize(self):
        """Initialize provider runtime resources."""

        self.authenticated = self.is_configured()
        return self.authenticated

    def shutdown(self):
        """Release provider runtime resources."""

        return True

    def validate_connection(self):
        """Validate provider configuration and connection state."""

        started = perf_counter()
        try:
            if not self.is_configured():
                raise AIProviderNotConfiguredError(f"{self.display_name or self.provider_id} is not configured.")
            self.statistics.last_connection_status = "Configured"
            self.statistics.last_error = ""
            return True
        except Exception as exc:
            self.statistics.failures += 1
            self.statistics.last_error = self.safe_error(exc)
            self.statistics.last_connection_status = "Failed"
            raise
        finally:
            self.statistics.last_checked_at = _timestamp()
            self.statistics.last_latency_ms = (perf_counter() - started) * 1000.0
            self.statistics.total_latency_ms += self.statistics.last_latency_ms

    def configuration_metadata(self):
        """Return JSON-safe configuration without leaking secrets."""

        metadata = {}
        for key, value in self.configuration.items():
            if "key" in key.lower() or "secret" in key.lower() or "token" in key.lower():
                metadata[key] = _masked(str(value))
            else:
                metadata[key] = value
        return metadata

    def safe_error(self, error):
        """Return a masked exception string."""

        message = str(error)
        for value in self.configuration.values():
            if isinstance(value, str) and value and ("key" in value.lower() or len(value) > 16):
                message = message.replace(value, _masked(value))
        return message

    @abstractmethod
    def execute(self, task, progress):
        """Execute an AI task using a real provider backend."""


class AIProviderRegistry:
    """Registers, discovers and selects production AI providers."""

    def __init__(self):
        self.providers = {}
        self.active_provider_id = ""

    def register(self, provider):
        """Register a provider instance exactly once."""

        if not isinstance(provider, AIProvider):
            raise TypeError("provider must inherit AIProvider")
        self.providers[provider.provider_id] = provider
        provider.initialize()
        if not self.active_provider_id:
            self.active_provider_id = provider.provider_id
        return provider

    def unregister(self, provider_id):
        """Unregister a provider."""

        provider = self.providers.pop(provider_id, None)
        if self.active_provider_id == provider_id:
            self.active_provider_id = next(iter(self.providers), "")
        return provider

    def switch(self, provider_id):
        """Switch active provider."""

        if provider_id not in self.providers:
            raise AIProviderNotConfiguredError(f"AI provider '{provider_id}' is not registered.")
        self.active_provider_id = provider_id
        return self.providers[provider_id]

    def discover(self):
        """Return registered provider metadata."""

        return [
            {
                "provider_id": provider.provider_id,
                "display_name": provider.display_name,
                "active": provider.provider_id == self.active_provider_id,
                "capabilities": provider.capabilities.to_dict(),
                "configured": provider.is_configured(),
                "authenticated": bool(provider.authenticated),
                "configuration": provider.configuration_metadata(),
                "statistics": provider.statistics.to_dict(),
            }
            for provider in self.providers.values()
        ]

    def provider_for(self, provider_id="", capability="chat"):
        """Return an active provider that supports the requested capability."""

        provider = self.providers.get(provider_id or self.active_provider_id)
        if provider is None:
            raise AIProviderNotConfiguredError("No production AI provider is configured.")
        if not provider.is_configured():
            raise AIProviderNotConfiguredError(f"AI provider '{provider.provider_id}' is not configured.")
        if capability and not provider.capabilities.supports(capability):
            raise AIProviderNotConfiguredError(
                f"AI provider '{provider.provider_id}' does not support capability '{capability}'."
            )
        return provider

    def initialize_all(self):
        """Initialize all registered providers."""

        return {provider_id: provider.initialize() for provider_id, provider in self.providers.items()}

    def validate_all(self):
        """Validate all configured providers and safely report failures."""

        report = {}
        for provider_id, provider in self.providers.items():
            try:
                report[provider_id] = {"ok": provider.validate_connection(), "error": ""}
            except Exception as exc:
                report[provider_id] = {"ok": False, "error": provider.safe_error(exc)}
        return report

    def shutdown_all(self):
        """Shutdown all registered providers."""

        return {provider_id: provider.shutdown() for provider_id, provider in self.providers.items()}

    def to_dict(self):
        """Return JSON-safe registry metadata."""

        return {
            "active_provider_id": self.active_provider_id,
            "providers": self.discover(),
        }

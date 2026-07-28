from engine.ai import AIEngine, AIProvider, AIProviderCapabilities, AIProviderNotConfiguredError
from engine.workspace.workspace import Workspace


class TestChatProvider(AIProvider):
    provider_id = "test-chat"
    display_name = "Test Chat Provider"

    @property
    def capabilities(self):
        return AIProviderCapabilities(chat=True, models=["test-model"])

    def execute(self, task, progress):
        progress(0.5, "processing")
        return {
            "provider": self.provider_id,
            "prompt": task.prompt,
            "workspace": task.context["workspace"]["name"],
        }


ai = AIEngine()

try:
    ai.execute("Create chair", Workspace())
    raise AssertionError("AIEngine must not simulate responses without a provider")
except AIProviderNotConfiguredError:
    pass

workspace = Workspace("AI Runtime Workspace")
session = ai.create_session("Runtime Session", workspace)
ai.register_provider(TestChatProvider())
ai.switch_provider("test-chat")
result = ai.execute("Summarize workspace", workspace, session=session)

assert result["provider"] == "test-chat"
assert result["workspace"] == "AI Runtime Workspace"
assert ai.diagnostics()["completed"] == 1
assert ai.diagnostics()["providers_registered"] >= 1
assert len(session.messages) == 2

print("ai-engine-production-ok")

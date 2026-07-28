from engine.ai import AIProviderNotConfiguredError
from engine.ai.assistant import AIAssistant


ai = AIAssistant()

try:
    ai.execute("Create a modern wooden chair")
    raise AssertionError("AIAssistant must not fabricate AI responses")
except AIProviderNotConfiguredError:
    pass

print("ai-assistant-production-ok")

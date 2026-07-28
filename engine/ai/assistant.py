from engine.ai.ai_engine import AIEngine


class AIAssistant:
    """Compatibility facade backed by the production AIEngine runtime."""

    def __init__(self, engine=None):
        self.engine = engine or AIEngine()

    def execute(self, prompt, workspace=None, session=None, provider_id="", capability="chat", background=False):
        """Execute a prompt through a registered production provider."""

        return self.engine.execute(prompt, workspace, session, provider_id, capability, background)

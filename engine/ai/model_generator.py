from engine.ai.runtime import AIProviderNotConfiguredError


class ModelGenerator:
    """Legacy facade retained for imports; real generation requires providers."""

    def generate(self, intent):
        """Reject simulated generation and require a production AI provider."""

        raise AIProviderNotConfiguredError(
            "Model generation requires a configured production AI provider."
        )

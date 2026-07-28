from engine.ai.runtime import AIProviderNotConfiguredError


class SketchToModel:
    """Legacy facade retained for imports; conversion requires a real provider."""

    def convert(self, sketch):
        """Reject simulated sketch-to-model conversion."""

        raise AIProviderNotConfiguredError(
            "Sketch-to-model conversion requires a configured production AI provider."
        )

from engine.ai.runtime import AIProviderNotConfiguredError


class ImageToSketch:
    """Legacy facade retained for imports; conversion requires a real provider."""

    def convert(self, image):
        """Reject simulated image-to-sketch conversion."""

        raise AIProviderNotConfiguredError(
            "Image-to-sketch conversion requires a configured production AI provider."
        )

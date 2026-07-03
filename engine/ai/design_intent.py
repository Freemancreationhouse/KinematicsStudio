from dataclasses import dataclass


@dataclass
class DesignIntent:

    workspace: str = "general"

    action: str = ""

    object_type: str = ""

    style: str = ""

    material: str = ""

    dimensions: dict = None

    confidence: float = 0.0

    prompt: str = ""

    def __post_init__(self):

        if self.dimensions is None:
            self.dimensions = {}

    def __repr__(self):

        return (
            f"DesignIntent("
            f"workspace={self.workspace}, "
            f"action={self.action}, "
            f"object={self.object_type}, "
            f"style={self.style}, "
            f"confidence={self.confidence:.2f})"
        )
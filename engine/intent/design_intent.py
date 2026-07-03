class DesignIntent:

    def __init__(self):

        self.shape = "unknown"

        self.workspace = "general"

        self.confidence = 0.0

        self.metadata = {}

    # -----------------------------

    def __repr__(self):

        return (

            f"Intent("

            f"shape={self.shape}, "

            f"workspace={self.workspace}, "

            f"confidence={self.confidence})"

        )
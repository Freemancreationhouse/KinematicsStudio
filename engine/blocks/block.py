from engine.geometry import Vector2


class Block:
    """Base metadata shared by block definitions."""

    def __init__(self, name, block_id=None, origin=None):

        self.id = block_id
        self.name = str(name).strip()
        self.origin = origin.copy() if origin is not None else Vector2()

    # --------------------------------

    @property
    def block_id(self):
        """Backward-compatible alias for the stable block ID."""

        return self.id

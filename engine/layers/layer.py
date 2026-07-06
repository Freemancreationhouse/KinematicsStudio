class Layer:
    """Describes display and edit properties shared by layer entities."""

    def __init__(
        self,
        name,
        color="#FFFFFF",
        layer_id=None,
        line_type="Continuous",
        line_weight=1.0,
    ):

        self.id = layer_id
        self.name = name
        self.color = color
        self.line_type = line_type
        self.line_weight = line_weight

        self.visible = True
        self.locked = False
        self.entities = []

    # --------------------------------

    def add(self, entity):
        """Track an entity that belongs to this layer."""

        if entity not in self.entities:
            self.entities.append(entity)

    # --------------------------------

    def remove(self, entity):
        """Remove a tracked entity from this layer."""

        if entity in self.entities:
            self.entities.remove(entity)

    # --------------------------------

    @property
    def count(self):

        return len(self.entities)

    # --------------------------------

    @property
    def linetype(self):
        """Backward-compatible alias for line_type."""

        return self.line_type

    @linetype.setter
    def linetype(self, value):

        self.line_type = value

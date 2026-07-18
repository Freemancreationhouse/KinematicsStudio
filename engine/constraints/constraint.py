from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QFont, QPen

from engine.geometry import BoundingBox, Vector2


GEOMETRIC_CONSTRAINTS = {
    "Horizontal",
    "Vertical",
    "Parallel",
    "Perpendicular",
    "Coincident",
    "Tangent",
    "Equal",
    "Concentric",
    "Symmetry",
    "Midpoint",
}

DIMENSIONAL_CONSTRAINTS = {
    "Distance",
    "Horizontal Distance",
    "Vertical Distance",
    "Radius",
    "Diameter",
    "Angle",
}


class Constraint:
    """Relationship between workspace entities owned by ConstraintManager."""

    def __init__(
        self,
        constraint_type,
        entities=None,
        value=None,
        name=None,
        constraint_id=None,
        driven=False,
    ):

        self.id = constraint_id
        self.constraint_type = str(constraint_type)
        self.name = name or self.constraint_type
        self.entities = list(entities or [])
        self.value = value
        self.driven = bool(driven)
        self.suppressed = False
        self.enabled = True
        self.selected = False
        self.status = "Unknown"
        self.message = ""

    # --------------------------------

    @property
    def type_name(self):
        """Return display type for property panels."""

        return f"{self.constraint_type} Constraint"

    # --------------------------------

    @property
    def is_constraint(self):
        """Return True for property/selection integration."""

        return True

    # --------------------------------

    @property
    def category(self):
        """Return Geometric or Dimensional category."""

        if self.constraint_type in DIMENSIONAL_CONSTRAINTS:
            return "Dimensional"

        return "Geometric"

    # --------------------------------

    @property
    def visible(self):
        """Constraints are visible unless suppressed."""

        return not self.suppressed

    # --------------------------------

    @property
    def locked(self):
        """Constraints are selectable and editable through commands."""

        return False

    # --------------------------------

    @property
    def bounding_box(self):
        """Return bounds around referenced entity geometry."""

        box = BoundingBox()

        for entity in self.entities:
            entity_box = getattr(entity, "bounding_box", None)

            if entity_box is not None:
                box.add(entity_box.min)
                box.add(entity_box.max)

        if box.min.x == float("inf"):
            box.add(Vector2())

        return box

    # --------------------------------

    def hit_test(self, point, tolerance=8.0):
        """Return True when a pick point is close to the constraint marker."""

        return self.marker_point().distance_to(point) <= tolerance

    # --------------------------------

    def marker_point(self):
        """Return a stable marker point near referenced geometry."""

        box = self.bounding_box

        return Vector2(
            (box.min.x + box.max.x) * 0.5,
            box.min.y - 14.0,
        )

    # --------------------------------

    def draw(self, painter):
        """Draw a lightweight constraint marker."""

        if not self.visible:
            return

        point = self.marker_point()
        color = "#ffeb3b" if self.selected else "#90caf9"

        painter.save()
        pen = QPen(QColor(color), 1)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(QColor(color))
        painter.drawEllipse(QPointF(point.x, point.y), 3.5, 3.5)

        font = QFont()
        font.setPointSizeF(8.0)
        painter.setFont(font)
        painter.drawText(QPointF(point.x + 6.0, point.y - 4.0), self.short_label())
        painter.restore()

    # --------------------------------

    def short_label(self):
        """Return a compact drawing label."""

        words = self.constraint_type.split()

        return "".join(word[:1].upper() for word in words)[:3]

    # --------------------------------

    def referenced_entity_count(self):
        """Return number of referenced entities."""

        return len(self.entities)

    # --------------------------------

    def references(self, entity):
        """Return True when the constraint references an entity."""

        return entity in self.entities

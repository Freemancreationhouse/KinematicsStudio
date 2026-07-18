import math

from engine.entities.entity import Entity
from engine.geometry import BoundingBox, Vector2
from engine.geometry.tolerance import GEOMETRY_EPSILON


class BlockReference(Entity):
    """Placed entity reference to a reusable BlockDefinition."""

    def __init__(
        self,
        definition=None,
        insertion_point=None,
        rotation=0.0,
        scale_x=1.0,
        scale_y=1.0,
    ):

        super().__init__()
        self.definition = definition
        self.definition_id = getattr(definition, "id", None)
        self.definition_name = getattr(definition, "name", None)
        self.insertion_point = insertion_point or Vector2()
        self.rotation = float(rotation)
        self.scale_x = float(scale_x)
        self.scale_y = float(scale_y)

    # --------------------------------

    def draw(self, painter):

        if not self.visible or self.definition is None:
            return

        painter.save()
        painter.translate(self.insertion_point.x, self.insertion_point.y)
        painter.rotate(self.rotation)
        painter.scale(self.scale_x, self.scale_y)
        painter.translate(-self.definition.origin.x, -self.definition.origin.y)

        for entity in self.definition.entities:
            if getattr(entity, "visible", True):
                entity.draw(painter)

        painter.restore()

    # --------------------------------

    def move(self, dx, dy):

        self.insertion_point.x += dx
        self.insertion_point.y += dy

    # --------------------------------

    def clone(self):

        clone = BlockReference(
            self.definition,
            self.insertion_point.copy(),
            self.rotation,
            self.scale_x,
            self.scale_y,
        )
        clone.selected = self.selected
        clone.visible = self.visible
        clone.locked = self.locked
        clone.layer = self.layer
        clone.layer_id = self.layer_id
        clone.layer_name = self.layer_name
        clone.color = self.color

        return clone

    # --------------------------------

    def exploded_entities(self):
        """Return transformed copies of entities contained by this reference."""

        if self.definition is None:
            return []

        return [
            self._transform_entity(entity)
            for entity in self.definition.entities
        ]

    # --------------------------------

    def hit_test(self, point):

        if self.definition is None:
            return False

        local_point = self._inverse_transform_point(point)

        return any(
            entity.hit_test(local_point)
            for entity in self.definition.entities
        )

    # --------------------------------

    @property
    def bounding_box(self):

        box = BoundingBox()

        if self.definition is None or not self.definition.entities:
            box.add(self.insertion_point)
            return box

        for entity in self.definition.entities:
            entity_box = entity.bounding_box

            for point in self._box_corners(entity_box):
                box.add(self._transform_point(point))

        return box

    # --------------------------------

    def _transform_point(self, point):

        origin = self.definition.origin if self.definition else Vector2()
        x = (point.x - origin.x) * self.scale_x
        y = (point.y - origin.y) * self.scale_y
        angle = math.radians(self.rotation)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        return Vector2(
            self.insertion_point.x + x * cos_a - y * sin_a,
            self.insertion_point.y + x * sin_a + y * cos_a,
        )

    # --------------------------------

    def _inverse_transform_point(self, point):

        origin = self.definition.origin if self.definition else Vector2()
        scale_x = self.scale_x if abs(self.scale_x) > GEOMETRY_EPSILON else 1.0
        scale_y = self.scale_y if abs(self.scale_y) > GEOMETRY_EPSILON else 1.0
        dx = point.x - self.insertion_point.x
        dy = point.y - self.insertion_point.y
        angle = math.radians(-self.rotation)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        return Vector2(
            origin.x + (dx * cos_a - dy * sin_a) / scale_x,
            origin.y + (dx * sin_a + dy * cos_a) / scale_y,
        )

    # --------------------------------

    def _box_corners(self, box):

        return (
            box.min,
            Vector2(box.max.x, box.min.y),
            box.max,
            Vector2(box.min.x, box.max.y),
        )

    # --------------------------------

    def _transform_entity(self, entity):

        if hasattr(entity, "start") and hasattr(entity, "end"):
            transformed = self._transform_line(entity)
        elif hasattr(entity, "p1") and hasattr(entity, "p2"):
            transformed = self._transform_rectangle(entity)
        elif hasattr(entity, "center") and hasattr(entity, "radius"):
            transformed = self._transform_circle(entity)
        elif isinstance(entity, BlockReference):
            transformed = self._transform_reference(entity)
        else:
            transformed = entity.clone()

        self._copy_entity_metadata(entity, transformed)

        return transformed

    # --------------------------------

    def _transform_line(self, entity):

        from engine.entities.line_entity import LineEntity

        return LineEntity(
            self._transform_point(entity.start),
            self._transform_point(entity.end),
        )

    # --------------------------------

    def _transform_rectangle(self, entity):

        from engine.entities.rectangle_entity import RectangleEntity

        points = [
            self._transform_point(point)
            for point in self._box_corners(entity.bounding_box)
        ]
        left = min(point.x for point in points)
        top = min(point.y for point in points)
        right = max(point.x for point in points)
        bottom = max(point.y for point in points)

        return RectangleEntity(Vector2(left, top), Vector2(right, bottom))

    # --------------------------------

    def _transform_circle(self, entity):

        from engine.entities.circle_entity import CircleEntity

        scale = (abs(self.scale_x) + abs(self.scale_y)) * 0.5

        return CircleEntity(
            self._transform_point(entity.center),
            entity.radius * scale,
        )

    # --------------------------------

    def _transform_reference(self, entity):

        return BlockReference(
            entity.definition,
            self._transform_point(entity.insertion_point),
            self.rotation + entity.rotation,
            self.scale_x * entity.scale_x,
            self.scale_y * entity.scale_y,
        )

    # --------------------------------

    def _copy_entity_metadata(self, source, target):

        target.selected = False
        target.visible = getattr(source, "visible", True)
        target.locked = getattr(source, "locked", False)
        target.layer = getattr(source, "layer", None)
        target.layer_id = getattr(source, "layer_id", None)
        target.layer_name = getattr(source, "layer_name", None)
        target.color = getattr(source, "color", None)

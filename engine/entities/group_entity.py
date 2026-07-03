from engine.entities.entity import Entity
from engine.geometry import BoundingBox


class GroupEntity(Entity):

    def __init__(self, entities=None):

        super().__init__()

        self.entities = entities[:] if entities else []

    # --------------------------------

    def add(self, entity):

        self.entities.append(entity)

    # --------------------------------

    def remove(self, entity):

        if entity in self.entities:

            self.entities.remove(entity)

    # --------------------------------

    def draw(self, painter):

        for entity in self.entities:

            if entity.visible:

                entity.draw(painter)

    # --------------------------------

    def move(self, dx, dy):

        for entity in self.entities:

            entity.move(dx, dy)

    # --------------------------------

    def clone(self):

        return GroupEntity(

            [e.clone() for e in self.entities]

        )

    # --------------------------------

    def hit_test(self, point):

        return any(

            e.hit_test(point)

            for e in self.entities

        )

    # --------------------------------

    @property
    def bounding_box(self):

        box = BoundingBox()

        for entity in self.entities:

            b = entity.bounding_box

            box.add(b.min)
            box.add(b.max)

        return box

    # --------------------------------

    @property
    def count(self):

        return len(self.entities)
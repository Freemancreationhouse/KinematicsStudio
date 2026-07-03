class SelectionManager:

    def __init__(self):

        self.selected = []

    # --------------------------------

    def clear(self):

        for entity in self.selected:

            entity.selected = False

        self.selected.clear()

    # --------------------------------

    def select(self, entity, additive=False):

        if not additive:

            self.clear()

        if entity not in self.selected:

            entity.selected = True

            self.selected.append(entity)

    # --------------------------------

    def deselect(self, entity):

        if entity in self.selected:

            entity.selected = False

            self.selected.remove(entity)

    # --------------------------------

    def toggle(self, entity):

        if entity in self.selected:

            self.deselect(entity)

        else:

            self.select(entity, True)

    # --------------------------------

    @property
    def count(self):

        return len(self.selected)

    # --------------------------------

    @property
    def first(self):

        if self.selected:

            return self.selected[0]

        return None
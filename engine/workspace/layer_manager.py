class Layer:

    def __init__(self, name="Layer"):

        self.name = name

        self.visible = True
        self.locked = False

        self.entities = []

    # --------------------------------

    def add(self, entity):

        self.entities.append(entity)

    # --------------------------------

    def remove(self, entity):

        if entity in self.entities:

            self.entities.remove(entity)

    # --------------------------------

    @property
    def count(self):

        return len(self.entities)


class LayerManager:

    def __init__(self):

        self.layers = []

        self.current = None

    # --------------------------------

    def create(self, name):

        layer = Layer(name)

        self.layers.append(layer)

        if self.current is None:

            self.current = layer

        return layer

    # --------------------------------

    def remove(self, layer):

        if layer in self.layers:

            self.layers.remove(layer)

            if self.current == layer:

                self.current = self.layers[0] if self.layers else None

    # --------------------------------

    def set_current(self, layer):

        if layer in self.layers:

            self.current = layer

    # --------------------------------

    @property

    def count(self):

        return len(self.layers)
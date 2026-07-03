from engine.layers.layer import Layer


class LayerManager:

    def __init__(self):

        self.layers = {}

        default = Layer("0", "#FFFFFF")

        self.layers["0"] = default

        self.current = default

    # ----------------------------

    def add(self, name, color="#FFFFFF"):

        if name in self.layers:
            return

        self.layers[name] = Layer(name, color)

    # ----------------------------

    def remove(self, name):

        if name == "0":
            return

        if name in self.layers:
            del self.layers[name]

    # ----------------------------

    def set_current(self, name):

        if name in self.layers:

            self.current = self.layers[name]

    # ----------------------------

    def get(self, name):

        return self.layers.get(name)

    # ----------------------------

    def names(self):

        return list(self.layers.keys())
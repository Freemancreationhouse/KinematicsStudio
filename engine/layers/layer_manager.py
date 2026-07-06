from engine.layers.layer import Layer


class LayerManager:
    """Owns workspace layers and tracks the current drawing layer."""

    def __init__(self):

        self.layers = []
        self._by_name = {}
        self._by_id = {}
        self._next_id = 0

        self.current = self.create("0")

    # ----------------------------

    def create(
        self,
        name,
        color="#FFFFFF",
        line_type="Continuous",
        line_weight=1.0,
    ):
        """Create a unique layer and return it."""

        if name in self._by_name:
            return self._by_name[name]

        layer = Layer(
            name=name,
            color=color,
            layer_id=self._next_id,
            line_type=line_type,
            line_weight=line_weight,
        )
        self._next_id += 1
        self.layers.append(layer)
        self._by_name[layer.name] = layer
        self._by_id[layer.id] = layer

        return layer

    # ----------------------------

    def add(self, name, color="#FFFFFF"):
        """Backward-compatible layer creation helper."""

        return self.create(name, color)

    # ----------------------------

    def remove(self, name):
        """Remove a non-default layer by name or object."""

        layer = self._coerce_layer(name)

        if layer is None or layer.name == "0":
            return

        self.layers.remove(layer)
        self._by_name.pop(layer.name, None)
        self._by_id.pop(layer.id, None)

        if self.current is layer:
            self.current = self._by_name["0"]

    # ----------------------------

    def rename(self, layer, new_name):
        """Rename a non-default layer while preserving its ID."""

        target = self._coerce_layer(layer)
        new_name = str(new_name).strip()

        if (
            target is None or
            target.name == "0" or
            not new_name or
            new_name in self._by_name
        ):
            return False

        self._by_name.pop(target.name, None)
        target.name = new_name
        self._by_name[target.name] = target

        for entity in list(target.entities):
            entity.layer_name = target.name

        return True

    # ----------------------------

    def set_properties(
        self,
        layer,
        color=None,
        line_type=None,
        line_weight=None,
    ):
        """Update display properties for an existing layer."""

        target = self._coerce_layer(layer)

        if target is None:
            return False

        if color is not None:
            target.color = str(color).strip() or target.color

        if line_type is not None:
            target.line_type = str(line_type).strip() or target.line_type

        if line_weight is not None:
            try:
                target.line_weight = max(0.0, float(line_weight))
            except (TypeError, ValueError):
                return False

        return True

    # ----------------------------

    def set_current(self, name):
        """Set the current layer by name or layer object."""

        layer = self._coerce_layer(name)

        if layer is not None:
            self.current = layer

    # ----------------------------

    def get(self, name):
        """Return a layer by name or ID."""

        if isinstance(name, int):
            return self._by_id.get(name)

        return self._by_name.get(name)

    # ----------------------------

    def get_by_id(self, layer_id):
        """Return a layer by numeric ID."""

        return self._by_id.get(layer_id)

    # ----------------------------

    def names(self):
        """Return all layer names in creation order."""

        return [layer.name for layer in self.layers]

    # ----------------------------

    @property
    def count(self):

        return len(self.layers)

    # ----------------------------

    def _coerce_layer(self, value):

        if isinstance(value, Layer):
            if value.name in self._by_name:
                return self._by_name[value.name]

            return None

        if isinstance(value, int):
            return self._by_id.get(value)

        return self._by_name.get(value)

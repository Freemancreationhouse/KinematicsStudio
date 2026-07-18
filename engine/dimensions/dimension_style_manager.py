from engine.dimensions.dimension_style import DimensionStyle


class DimensionStyleManager:
    """Owns dimension styles and tracks the current style for new dimensions."""

    DEFAULT_NAME = "Standard"

    def __init__(self):

        self.styles = []
        self._by_name = {}
        self._by_id = {}
        self._next_id = 0

        self.current = self.create(self.DEFAULT_NAME)

    # --------------------------------

    def create(
        self,
        name,
        text_height=20.0,
        arrow_size=10.0,
        extension_offset=6.0,
        extension_overshoot=6.0,
        precision=2,
        units="Decimal",
        text_gap=4.0,
    ):
        """Create a uniquely named dimension style and return it."""

        name = str(name).strip() or self._next_name()

        if name in self._by_name:
            return self._by_name[name]

        style = DimensionStyle(
            name=name,
            style_id=self._next_id,
            text_height=text_height,
            arrow_size=arrow_size,
            extension_offset=extension_offset,
            extension_overshoot=extension_overshoot,
            precision=precision,
            units=units,
            text_gap=text_gap,
        )
        self._next_id += 1
        self.styles.append(style)
        self._by_name[style.name] = style
        self._by_id[style.id] = style

        return style

    # --------------------------------

    def remove(self, style):
        """Remove a non-default style."""

        target = self._coerce_style(style)

        if target is None or target.name == self.DEFAULT_NAME:
            return False

        self.styles.remove(target)
        self._by_name.pop(target.name, None)
        self._by_id.pop(target.id, None)

        if self.current is target:
            self.current = self._by_name[self.DEFAULT_NAME]

        return True

    # --------------------------------

    def rename(self, style, new_name):
        """Rename a non-default style while preserving its ID."""

        target = self._coerce_style(style)
        new_name = str(new_name).strip()

        if (
            target is None or
            target.name == self.DEFAULT_NAME or
            not new_name or
            new_name in self._by_name
        ):
            return False

        self._by_name.pop(target.name, None)
        target.name = new_name
        self._by_name[target.name] = target

        return True

    # --------------------------------

    def set_current(self, style):
        """Set the current style by name, ID, or object."""

        target = self._coerce_style(style)

        if target is not None:
            self.current = target
            return True

        return False

    # --------------------------------

    def get(self, name):
        """Return a style by name or ID."""

        if isinstance(name, int):
            return self._by_id.get(name)

        return self._by_name.get(name)

    # --------------------------------

    def get_by_id(self, style_id):
        """Return a style by numeric ID."""

        return self._by_id.get(style_id)

    # --------------------------------

    def names(self):
        """Return all style names in creation order."""

        return [style.name for style in self.styles]

    # --------------------------------

    def _coerce_style(self, value):

        if isinstance(value, DimensionStyle):
            return self._by_id.get(value.id)

        if isinstance(value, int):
            return self._by_id.get(value)

        return self._by_name.get(value)

    # --------------------------------

    def _next_name(self):

        index = 1

        while f"Dimension Style {index}" in self._by_name:
            index += 1

        return f"Dimension Style {index}"

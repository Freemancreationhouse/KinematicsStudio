class DimensionStyle:
    """Display settings shared by dimension entities."""

    def __init__(
        self,
        name="Standard",
        style_id=None,
        text_height=20.0,
        arrow_size=10.0,
        extension_offset=6.0,
        extension_overshoot=6.0,
        precision=2,
        units="Decimal",
        text_gap=4.0,
    ):

        self.id = style_id
        self.name = name
        self.text_height = float(text_height)
        self.arrow_size = float(arrow_size)
        self.extension_offset = float(extension_offset)
        self.extension_overshoot = float(extension_overshoot)
        self.precision = int(precision)
        self.units = units
        self.text_gap = float(text_gap)

    # --------------------------------

    def clone(self):
        """Return a copy preserving style values without manager identity."""

        return DimensionStyle(
            self.name,
            self.id,
            self.text_height,
            self.arrow_size,
            self.extension_offset,
            self.extension_overshoot,
            self.precision,
            self.units,
            self.text_gap,
        )

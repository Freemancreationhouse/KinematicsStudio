class Pattern:
    """Defines hatch pattern metadata used by HatchEntity rendering."""

    def __init__(self, name, pattern_type="lines", scale=10.0, angle=45.0):

        self.name = name
        self.pattern_type = pattern_type
        self.scale = float(scale)
        self.angle = float(angle)

    # --------------------------------

    @property
    def is_solid(self):
        """Return True when this pattern should render as a solid fill."""

        return self.pattern_type == "solid"

    # --------------------------------

    def clone(self):
        """Return a copy of the pattern definition."""

        return Pattern(self.name, self.pattern_type, self.scale, self.angle)

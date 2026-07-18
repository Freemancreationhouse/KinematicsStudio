from engine.patterns.pattern import Pattern


class PatternManager:
    """Owns hatch pattern definitions for a workspace."""

    def __init__(self):

        self.patterns = []
        self._by_name = {}
        self.current = None
        self._register_defaults()

    # --------------------------------

    def register(self, pattern):
        """Register a hatch pattern by name."""

        existing = self._by_name.get(pattern.name)

        if existing is not None:
            return existing

        self.patterns.append(pattern)
        self._by_name[pattern.name] = pattern

        if self.current is None:
            self.current = pattern

        return pattern

    # --------------------------------

    def create(self, name, pattern_type="lines", scale=10.0, angle=45.0):
        """Create and register a pattern definition."""

        return self.register(Pattern(name, pattern_type, scale, angle))

    # --------------------------------

    def get(self, name):
        """Return a pattern by name."""

        return self._by_name.get(name)

    # --------------------------------

    def set_current(self, pattern):
        """Set the current hatch pattern by name or object."""

        target = pattern if isinstance(pattern, Pattern) else self.get(pattern)

        if target is not None:
            self.current = target
            return True

        return False

    # --------------------------------

    def names(self):
        """Return registered pattern names."""

        return [pattern.name for pattern in self.patterns]

    # --------------------------------

    def _register_defaults(self):

        self.register(Pattern("SOLID", "solid", 1.0, 0.0))
        self.register(Pattern("ANSI31", "lines", 10.0, 45.0))
        self.register(Pattern("ANSI32", "lines", 10.0, 0.0))

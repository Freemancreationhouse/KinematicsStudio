class GCodeGenerator:

    def __init__(self):

        self.lines = []

    # --------------------------------

    def clear(self):

        self.lines.clear()

    # --------------------------------

    def add(self, line):

        self.lines.append(line)

    # --------------------------------

    def generate_header(self):

        self.add("G21")
        self.add("G90")
        self.add("G17")

    # --------------------------------

    def generate_footer(self):

        self.add("M5")
        self.add("G0 X0 Y0")
        self.add("M30")

    # --------------------------------

    def export(self):

        return "\n".join(self.lines)
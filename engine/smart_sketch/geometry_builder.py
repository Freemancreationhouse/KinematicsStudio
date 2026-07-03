from engine.generator.geometry_generator import GeometryGenerator


class GeometryBuilder:

    def __init__(self):

        self.generator = GeometryGenerator()

    # -----------------------------------

    def build(self, intent, stroke):

        return self.generator.generate(

            intent,

            stroke

        )
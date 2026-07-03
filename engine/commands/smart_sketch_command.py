from engine.commands.add_command import AddCommand


class SmartSketchCommand(AddCommand):

    def __init__(self, project, entity):

        super().__init__(project, entity)
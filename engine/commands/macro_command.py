from engine.commands.command import Command


class MacroCommand(Command):

    def __init__(self, name="Macro"):

        self._name = name
        self.commands = []

    # --------------------------------

    def add(self, command):

        self.commands.append(command)

    # --------------------------------

    def execute(self):

        for command in self.commands:

            command.execute()

    # --------------------------------

    def undo(self):

        for command in reversed(self.commands):

            command.undo()

    # --------------------------------

    @property
    def name(self):

        return self._name
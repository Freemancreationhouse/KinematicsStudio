from engine.commands import Command, CommandManager


class TestCommand(Command):

    def __init__(self):

        self.value = 0

    def execute(self):

        self.value += 1

    def undo(self):

        self.value -= 1


manager = CommandManager()

cmd = TestCommand()

manager.execute(cmd)

print(cmd.value)

manager.undo()

print(cmd.value)

manager.redo()

print(cmd.value)

print(manager.undo_count)

print(manager.redo_count)
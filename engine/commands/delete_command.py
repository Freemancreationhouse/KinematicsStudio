from engine.commands.command import Command


class DeleteCommand(Command):

    def __init__(self, project, entity):

        self.project = project
        self.entity = entity

    def execute(self):

        self.project.remove(self.entity)

    def undo(self):

        self.project.add(self.entity)
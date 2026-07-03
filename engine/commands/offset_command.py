class OffsetCommand:

    def __init__(self, project, entity):

        self.project = project
        self.entity = entity

    def execute(self):

        self.project.add(self.entity)

    def undo(self):

        self.project.remove(self.entity)
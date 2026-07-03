class TrimCommand:

    def __init__(self, project, old_line, new_lines):

        self.project = project
        self.old_line = old_line
        self.new_lines = new_lines

    def execute(self):

        if self.old_line in self.project.entities:
            self.project.remove(self.old_line)

        for line in self.new_lines:
            self.project.add(line)

    def undo(self):

        for line in self.new_lines:

            if line in self.project.entities:
                self.project.remove(line)

        self.project.add(self.old_line)
class CommandManager:

    def __init__(self):

        self.undo_stack = []
        self.redo_stack = []
        self.on_change = None

    # --------------------------------

    def execute(self, command):

        command.execute()

        self.record(command)

    # --------------------------------

    def record(self, command):

        self.undo_stack.append(command)

        self.redo_stack.clear()

        self._changed()

    # --------------------------------

    def undo(self):

        if not self.undo_stack:

            return None

        command = self.undo_stack.pop()

        command.undo()

        self.redo_stack.append(command)

        self._changed()

        return command

    # --------------------------------

    def redo(self):

        if not self.redo_stack:

            return None

        command = self.redo_stack.pop()

        command.execute()

        self.undo_stack.append(command)

        self._changed()

        return command

    # --------------------------------

    def history(self):

        return list(self.undo_stack)

    # --------------------------------

    @property
    def undo_available(self):

        return bool(self.undo_stack)

    @property
    def redo_available(self):

        return bool(self.redo_stack)

    # --------------------------------

    def _changed(self):

        if self.on_change:
            self.on_change(self)

    # --------------------------------

    @property
    def undo_count(self):

        return len(self.undo_stack)

    @property
    def redo_count(self):

        return len(self.redo_stack)

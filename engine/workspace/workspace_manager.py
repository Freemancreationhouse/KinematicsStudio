from .workspace import Workspace


class WorkspaceManager:

    def __init__(self):

        self.workspaces = {}

        self.active = None

    # --------------------------------

    def create(self, name):

        ws = Workspace(name)

        self.workspaces[name] = ws

        if self.active is None:

            self.active = ws

        return ws

    # --------------------------------

    def remove(self, name):

        if name in self.workspaces:

            del self.workspaces[name]

            if self.active and self.active.name == name:

                self.active = None

    # --------------------------------

    def set_active(self, name):

        if name in self.workspaces:

            self.active = self.workspaces[name]

    # --------------------------------

    def get(self, name):

        return self.workspaces.get(name)

    # --------------------------------

    @property
    def names(self):

        return list(self.workspaces.keys())
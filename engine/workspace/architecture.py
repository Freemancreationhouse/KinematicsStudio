from engine.workspace.base_workspace import BaseWorkspace


class ArchitectureWorkspace(BaseWorkspace):

    NAME = "architecture"

    OBJECTS = {

        "building",
        "wall",
        "door",
        "window",
        "column",
        "stair"

    }

    def can_handle(self, intent):

        return intent.object_type in self.OBJECTS

    def generate(self, intent):

        return {

            "workspace": self.NAME,

            "object": intent.object_type,

            "status": "accepted"

        }
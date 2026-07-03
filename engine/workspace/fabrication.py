from engine.workspace.base_workspace import BaseWorkspace


class FabricationWorkspace(BaseWorkspace):

    NAME = "fabrication"

    OBJECTS = {

        "gcode",
        "toolpath",
        "laser"

    }

    def can_handle(self, intent):

        return intent.object_type in self.OBJECTS

    def generate(self, intent):

        return {

            "workspace": self.NAME,

            "object": intent.object_type,

            "status": "accepted"

        }
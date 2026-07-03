from engine.workspace.base_workspace import BaseWorkspace


class LandscapeWorkspace(BaseWorkspace):

    NAME = "landscape"

    OBJECTS = {

        "terrain",
        "garden",
        "park"

    }

    def can_handle(self, intent):

        return intent.object_type in self.OBJECTS

    def generate(self, intent):

        return {

            "workspace": self.NAME,

            "object": intent.object_type,

            "status": "accepted"

        }
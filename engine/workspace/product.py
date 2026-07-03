from engine.workspace.base_workspace import BaseWorkspace


class ProductWorkspace(BaseWorkspace):

    NAME = "product"

    OBJECTS = {

        "lamp",
        "bottle",
        "phone",
        "speaker"

    }

    def can_handle(self, intent):

        return intent.object_type in self.OBJECTS

    def generate(self, intent):

        return {

            "workspace": self.NAME,

            "object": intent.object_type,

            "status": "accepted"

        }
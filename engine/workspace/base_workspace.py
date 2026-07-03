class BaseWorkspace:

    NAME = "general"

    def can_handle(self, intent):

        return False

    def generate(self, intent):

        raise NotImplementedError
class ModuleManager:

    def __init__(self):

        self.modules = {}

    # ---------------------------------

    def register(self, name, module):

        self.modules[name] = module

    # ---------------------------------

    def get(self, name):

        return self.modules.get(name)

    # ---------------------------------

    def exists(self, name):

        return name in self.modules

    # ---------------------------------

    def remove(self, name):

        if name in self.modules:

            del self.modules[name]

    # ---------------------------------

    def clear(self):

        self.modules.clear()


modules = ModuleManager()
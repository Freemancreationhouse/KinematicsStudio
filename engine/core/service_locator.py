class ServiceLocator:

    def __init__(self):

        self._services = {}

    # ------------------------------

    def register(self, name, service):

        self._services[name] = service

    # ------------------------------

    def get(self, name):

        return self._services.get(name)

    # ------------------------------

    def has(self, name):

        return name in self._services

    # ------------------------------

    def clear(self):

        self._services.clear()


services = ServiceLocator()
class EventRouter:

    def __init__(self):

        self.handlers = {}

    def register(self, name, handler):

        self.handlers[name] = handler

    def dispatch(self, name, *args, **kwargs):

        if name in self.handlers:

            return self.handlers[name](*args, **kwargs)

        return None
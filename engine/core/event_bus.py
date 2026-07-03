class EventBus:

    def __init__(self):

        self._listeners = {}

    # ---------------------------------

    def subscribe(self, event_name, callback):

        self._listeners.setdefault(event_name, []).append(callback)

    # ---------------------------------

    def emit(self, event_name, *args, **kwargs):

        for callback in self._listeners.get(event_name, []):

            callback(*args, **kwargs)

    # ---------------------------------

    def unsubscribe(self, event_name, callback):

        if event_name not in self._listeners:
            return

        if callback in self._listeners[event_name]:

            self._listeners[event_name].remove(callback)


events = EventBus()
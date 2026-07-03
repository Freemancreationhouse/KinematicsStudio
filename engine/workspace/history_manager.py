class HistoryManager:

    def __init__(self):

        self.entries = []

    # --------------------------------

    def add(self, action):

        self.entries.append(action)

    # --------------------------------

    def clear(self):

        self.entries.clear()

    # --------------------------------

    @property
    def count(self):

        return len(self.entries)

    # --------------------------------

    @property
    def last(self):

        if self.entries:

            return self.entries[-1]

        return None
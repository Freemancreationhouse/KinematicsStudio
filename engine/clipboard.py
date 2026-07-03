class Clipboard:

    def __init__(self):

        self.entity = None

    def copy(self, entity):

        self.entity = entity

    def paste(self):

        return self.entity
class Project:

    def __init__(self):
        self.entities = []

    def add_entity(self, entity):
        self.entities.append(entity)

    def clear(self):
        self.entities.clear()
from abc import ABC, abstractmethod


class Command(ABC):

    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def undo(self):
        pass

    @property
    def name(self):

        return self.__class__.__name__
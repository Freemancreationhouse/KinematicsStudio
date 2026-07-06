from engine.commands.command_manager import CommandManager
from engine.clipboard import Clipboard
from engine.layers.layer_manager import LayerManager


class Project:

    def __init__(self):

        self.entities = []

        self.selected = None

        self.command_manager = CommandManager()

        self.clipboard = Clipboard()

        self.layer_manager = LayerManager()

        self.selection_changed_callbacks = []

    # ------------------------------------

    def add(self, entity):

        layer = self.layer_manager.current

        if getattr(entity, "layer", None) is None:
            entity.layer = layer
            entity.layer_id = layer.id
            entity.layer_name = layer.name
            layer.add(entity)

        self.entities.append(entity)

    # ------------------------------------

    def remove(self, entity):

        if entity in self.entities:

            self.entities.remove(entity)

        layer = getattr(entity, "layer", None)

        if layer is not None and hasattr(layer, "remove"):
            layer.remove(entity)

        if self.selected == entity:

            self.selected = None

        self.notify_selection_changed()

    # ------------------------------------

    def clear_selection(self):

        if self.selected:

            self.selected.selected = False

        self.selected = None

        self.notify_selection_changed()

    # ------------------------------------

    def select(self, entity):

        self.clear_selection()

        self.selected = entity

        if entity:

            entity.selected = True

        self.notify_selection_changed()

    # ------------------------------------

    def on_selection_changed(self, callback):

        self.selection_changed_callbacks.append(callback)

    # ------------------------------------

    def notify_selection_changed(self):

        for callback in self.selection_changed_callbacks:

            callback(self.selected)

    # ------------------------------------

    def undo(self):

        self.command_manager.undo()

        self.notify_selection_changed()

    # ------------------------------------

    def redo(self):

        self.command_manager.redo()

        self.notify_selection_changed()

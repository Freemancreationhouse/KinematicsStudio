from engine.commands import CommandManager
from engine.blocks import BlockManager
from engine.layers.layer_manager import LayerManager
from engine.workspace.selection_manager import SelectionManager


class WorkspaceEntityList(list):
    """List that assigns workspace layer metadata as entities are stored."""

    def __init__(self, workspace):

        super().__init__()
        self.workspace = workspace

    # --------------------------------

    def append(self, entity):

        self.workspace.assign_layer(entity)
        super().append(entity)

    # --------------------------------

    def insert(self, index, entity):

        self.workspace.assign_layer(entity)
        super().insert(index, entity)

    # --------------------------------

    def extend(self, entities):

        for entity in entities:
            self.append(entity)

    # --------------------------------

    def remove(self, entity):

        self.workspace.unregister_layer_entity(entity)
        super().remove(entity)

    # --------------------------------

    def pop(self, index=-1):

        entity = super().pop(index)
        self.workspace.unregister_layer_entity(entity)

        return entity

    # --------------------------------

    def clear(self):

        for entity in list(self):
            self.workspace.unregister_layer_entity(entity)

        super().clear()


class Workspace:
    """Owns model entities, selection state, and command history."""

    def __init__(self, name="Workspace"):

        self.name = name

        self.layer_manager = LayerManager()
        self.layers = self.layer_manager
        self.block_manager = BlockManager()
        self.blocks = self.block_manager
        self.entities = WorkspaceEntityList(self)

        self.selection = SelectionManager()

        self.command_manager = CommandManager()

    # --------------------------------

    def add_entity(self, entity):
        """Store an entity in this workspace."""

        self.entities.append(entity)

    # --------------------------------

    def remove_entity(self, entity):
        """Remove an entity from this workspace if present."""

        if entity in self.entities:

            self.entities.remove(entity)

    # --------------------------------

    def clear(self):
        """Remove all entities from this workspace."""

        self.entities.clear()

    # --------------------------------

    def visible_entities(self):
        """Return entities currently available for rendering and snapping."""

        return [
            entity for entity in self.entities
            if getattr(entity, "visible", True) and self.entity_layer_visible(entity)
        ]

    # --------------------------------

    def selectable_entities(self):
        """Return visible entities that are not locked."""

        return [
            entity for entity in self.visible_entities()
            if (
                not getattr(entity, "locked", False) and
                not self.entity_layer_locked(entity)
            )
        ]

    # --------------------------------

    def bounds(self):
        """Return the combined bounding box of visible entities."""

        visible = self.visible_entities()

        if not visible:
            return None

        from engine.geometry import BoundingBox

        bounds = BoundingBox()

        for entity in visible:
            box = entity.bounding_box
            bounds.add(box.min)
            bounds.add(box.max)

        return bounds

    # --------------------------------

    def snap_candidates(self):
        """Return visible entities that can participate in snapping."""

        return self.visible_entities()

    # --------------------------------

    @property
    def current_layer(self):
        """Return the current layer used for new entities."""

        return self.layer_manager.current

    # --------------------------------

    def set_current_layer(self, layer):
        """Set the current layer by layer name, ID, or object."""

        self.layer_manager.set_current(layer)

    # --------------------------------

    def create_layer(
        self,
        name,
        color="#FFFFFF",
        line_type="Continuous",
        line_weight=1.0,
    ):
        """Create a layer through the workspace-owned manager."""

        return self.layer_manager.create(
            name,
            color,
            line_type,
            line_weight
        )

    # --------------------------------

    def rename_layer(self, layer, new_name):
        """Rename a workspace layer."""

        return self.layer_manager.rename(layer, new_name)

    # --------------------------------

    def update_layer_properties(
        self,
        layer,
        color=None,
        line_type=None,
        line_weight=None,
    ):
        """Update layer display properties."""

        changed = self.layer_manager.set_properties(
            layer,
            color,
            line_type,
            line_weight
        )

        if changed:
            target = self.layer_manager._coerce_layer(layer)

            for entity in list(getattr(target, "entities", [])):
                entity.color = target.color

        return changed

    # --------------------------------

    def delete_layer(self, layer):
        """Delete a non-default layer and move its entities to Layer 0."""

        target = self.layer_manager._coerce_layer(layer)
        default = self.layer_manager.get("0")

        if target is None or target is default:
            return False

        for entity in list(self.entities):
            if self._entity_layer(entity) is target:
                self.assign_layer(entity, default)

        self.layer_manager.remove(target)

        return True

    # --------------------------------

    def assign_layer(self, entity, layer=None):
        """Assign an entity to a layer when it has no valid layer."""

        target = layer or self._entity_layer(entity) or self.current_layer

        if target is None:
            return entity

        self.unregister_layer_entity(entity)
        entity.layer = target
        entity.layer_id = target.id
        entity.layer_name = target.name
        entity.color = target.color
        target.add(entity)

        return entity

    # --------------------------------

    def assign_replacement_layer(self, source, replacements):
        """Assign replacement entities to the same layer as their source."""

        layer = self._entity_layer(source) or self.current_layer

        for entity in replacements:
            self.assign_layer(entity, layer)

        return replacements

    # --------------------------------

    def unregister_layer_entity(self, entity):
        """Remove an entity from the layer tracking list if needed."""

        layer = self._entity_layer(entity)

        if layer is not None:
            layer.remove(entity)

    # --------------------------------

    def entity_layer(self, entity):
        """Return the layer assigned to an entity."""

        return self._entity_layer(entity)

    # --------------------------------

    def entity_layer_visible(self, entity):
        """Return True when the entity's layer is visible."""

        layer = self._entity_layer(entity)

        return True if layer is None else layer.visible

    # --------------------------------

    def entity_layer_locked(self, entity):
        """Return True when the entity's layer is locked."""

        layer = self._entity_layer(entity)

        return False if layer is None else layer.locked

    # --------------------------------

    def _entity_layer(self, entity):

        layer = getattr(entity, "layer", None)

        if layer is not None and self.layer_manager.get_by_id(layer.id) is layer:
            return layer

        layer_id = getattr(entity, "layer_id", None)

        if layer_id is not None:
            layer = self.layer_manager.get_by_id(layer_id)

            if layer is not None:
                return layer

        layer_name = getattr(entity, "layer_name", None)

        if layer_name:
            return self.layer_manager.get(layer_name)

        return None

    # --------------------------------

    @property
    def count(self):

        return len(self.entities)

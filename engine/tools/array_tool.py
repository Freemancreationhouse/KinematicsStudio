from engine.commands import ArrayEntityCommand
from engine.geometry.array import (
    preview_rectangular_array,
    rectangular_array_entities,
)
from engine.tools.entity_pick import hit_entity
from engine.tools.tool import Tool


class ArrayTool(Tool):
    """Create rectangular arrays of selected geometry."""

    def __init__(self):

        super().__init__()

        self.entities = []
        self.base_point = None
        self.preview = []
        self.rows = 2
        self.columns = 2
        self.row_spacing = 0.0
        self.column_spacing = 0.0
        self.input_mode = "rows"
        self.input_text = ""
        self.status_text = "Array: Select entities"

    # --------------------------------

    def deactivate(self):

        self.cancel()

    # --------------------------------

    def mouse_press(self, workspace, point, additive=False):

        if workspace is None:
            return

        if not self.entities:
            self._load_or_pick_entities(workspace, point, additive)
            return

        if self.base_point is None:
            self.base_point = point
            self.status_text = self._spacing_status()
            return

        self._sync_spacing(point)
        array_entities = self._array_entities()

        if not array_entities:
            self.status_text = "Array: No array available"
            return

        workspace.command_manager.execute(
            ArrayEntityCommand(workspace, array_entities)
        )
        self.cancel()

    # --------------------------------

    def mouse_move(self, workspace, point):

        if not self.entities or self.base_point is None:
            return

        self._sync_spacing(point)
        self.preview = self._preview_entities()
        self.status_text = self._spacing_status()

    # --------------------------------

    def mouse_release(self, workspace, point, additive=False):

        pass

    # --------------------------------

    def draw_preview(self, painter):

        for entity in self.preview:
            previous = getattr(entity, "selected", False)
            entity.selected = True
            entity.draw(painter)
            entity.selected = previous

    # --------------------------------

    def key_press(self, workspace, key):

        if key in ("Escape", "Esc", 0x01000000):
            self.cancel()
            return

        if key in ("Backspace", 0x01000003):
            self.input_text = self.input_text[:-1]
            self._sync_input()
            return

        character = self._key_character(key)

        if character is None:
            return

        if character in "Rr":
            self._set_input_mode("rows")
            return

        if character in "Cc":
            self._set_input_mode("columns")
            return

        if character.isdigit():
            self.input_text += character
            self._sync_input()

    # --------------------------------

    def cancel(self):

        self.entities = []
        self.base_point = None
        self.preview = []
        self.rows = 2
        self.columns = 2
        self.row_spacing = 0.0
        self.column_spacing = 0.0
        self.input_mode = "rows"
        self.input_text = ""
        self.status_text = "Array: Select entities"

    # --------------------------------

    def _load_or_pick_entities(self, workspace, point, additive):

        selection = getattr(workspace, "selection", None)
        selected = list(selection.selected) if selection else []
        hit = hit_entity(workspace, point)

        if selected and hit is None:
            self.entities = selected
            self.base_point = point
            self.status_text = self._spacing_status()
            return

        if hit is not None:
            if selection:
                selection.select(hit, additive)

            if additive and selected:
                self.entities = list(selection.selected)
            elif selected and hit in selected:
                self.entities = selected
            else:
                self.entities = [hit]

            self.status_text = f"Array: Selected {len(self.entities)}. Pick base point"
            return

        if selected:
            self.entities = selected
            self.status_text = f"Array: Selected {len(self.entities)}. Pick base point"
            return

        self.status_text = "Array: Select entities"

    # --------------------------------

    def _sync_spacing(self, point):

        self.column_spacing = point.x - self.base_point.x
        self.row_spacing = point.y - self.base_point.y

    # --------------------------------

    def _array_entities(self):

        generated = []

        for entity in self.entities:
            generated.extend(
                rectangular_array_entities(
                    entity,
                    self.rows,
                    self.columns,
                    self.row_spacing,
                    self.column_spacing
                )
            )

        return generated

    # --------------------------------

    def _preview_entities(self):

        preview = []

        for entity in self.entities:
            preview.extend(
                preview_rectangular_array(
                    entity,
                    self.rows,
                    self.columns,
                    self.row_spacing,
                    self.column_spacing
                )
            )

        return preview

    # --------------------------------

    def _set_input_mode(self, mode):

        self.input_mode = mode
        self.input_text = ""
        self.status_text = self._input_status()

    # --------------------------------

    def _sync_input(self):

        value = int(self.input_text) if self.input_text else 1
        value = max(1, value)

        if self.input_mode == "rows":
            self.rows = value
        else:
            self.columns = value

        self.preview = self._preview_entities()
        self.status_text = self._input_status()

    # --------------------------------

    def _input_status(self):

        return (
            f"Array: {self.input_mode.title()}={self.input_text or 1}; "
            f"R={self.rows} C={self.columns}"
        )

    # --------------------------------

    def _spacing_status(self):

        return (
            f"Array: R={self.rows} C={self.columns} "
            f"Row spacing={self.row_spacing:.2f} "
            f"Column spacing={self.column_spacing:.2f}"
        )

    # --------------------------------

    def _key_character(self, key):

        key_text = str(key)

        if len(key_text) == 1 and key_text.isalnum():
            return key_text

        if isinstance(key, int):
            if 48 <= key <= 57:
                return chr(key)

            if 65 <= key <= 90:
                return chr(key)

        return None

from engine.tools.entity_pick import entity_distance
from engine.tools.tool import Tool


class CornerModifyTool(Tool):
    """Shared interaction flow for two-line corner modify tools."""

    operation_name = "Corner"
    value_name = "Value"
    default_value = 5.0
    command_class = None

    def __init__(self):

        super().__init__()

        self.first = None
        self.second = None
        self.first_pick = None
        self.second_pick = None
        self.preview = []
        self.value = self.default_value
        self.value_text = ""
        self.status_text = f"{self.operation_name}: Select first line"

    # --------------------------------

    def deactivate(self):

        self.cancel()

    # --------------------------------

    def mouse_press(self, workspace, point, additive=False):

        if workspace is None:
            return

        if self.first is not None and self.second is not None:
            self._confirm(workspace)
            return

        entity = self._hit(workspace, point)

        if entity is None or not self._is_line(entity):
            return

        if self.first is None:
            self.first = entity
            self.first_pick = point
            self.status_text = f"{self.operation_name}: Select second line"
            return

        if entity is self.first:
            self.cancel()
            return

        self.second = entity
        self.second_pick = point
        self.preview = self._preview_entities()
        self.status_text = self._value_status()

    # --------------------------------

    def mouse_move(self, workspace, point):

        if self.first is None or self.second is None:
            return

        self.preview = self._preview_entities()

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

        if key in ("Enter", "Return", 0x01000004, 0x01000005):
            self._confirm(workspace)
            return

        if key in ("Backspace", 0x01000003):
            self.value_text = self.value_text[:-1]
            self._sync_value()
            return

        character = self._key_character(key)

        if character is None:
            return

        self.value_text += character
        self._sync_value()

    # --------------------------------

    def cancel(self):

        self.first = None
        self.second = None
        self.first_pick = None
        self.second_pick = None
        self.preview = []
        self.value = self.default_value
        self.value_text = ""
        self.status_text = f"{self.operation_name}: Select first line"

    # --------------------------------

    def _confirm(self, workspace):

        if self.first is None or self.second is None:
            return

        replacements = self._replacement_entities()

        if not replacements:
            self.status_text = f"{self.operation_name}: No solution available"
            return

        workspace.command_manager.execute(
            self.command_class(
                workspace,
                [self.first, self.second],
                replacements
            )
        )
        self.cancel()

    # --------------------------------

    def _sync_value(self):

        try:
            self.value = float(self.value_text) if self.value_text else self.default_value
        except ValueError:
            self.value = self.default_value

        self.preview = self._preview_entities()
        self.status_text = self._value_status()

    # --------------------------------

    def _value_status(self):

        return f"{self.operation_name}: {self.value_name} {self.value:g}; Enter to confirm"

    # --------------------------------

    def _hit(self, workspace, point):

        candidates = (
            workspace.selectable_entities()
            if hasattr(workspace, "selectable_entities")
            else workspace.entities
        )
        best = None
        best_distance = 8.0

        for entity in reversed(candidates):
            distance = entity_distance(entity, point)

            if distance is not None and distance < best_distance:
                best = entity
                best_distance = distance

        return best

    # --------------------------------

    def _is_line(self, entity):

        return hasattr(entity, "start") and hasattr(entity, "end")

    # --------------------------------

    def _key_character(self, key):

        key_text = str(key)

        if len(key_text) == 1 and (
            key_text.isdigit() or key_text in "."
        ):
            return key_text

        if isinstance(key, int):
            if 48 <= key <= 57:
                return chr(key)

            if key == 46:
                return "."

        return None

    # --------------------------------

    def _preview_entities(self):

        return []

    # --------------------------------

    def _replacement_entities(self):

        return []

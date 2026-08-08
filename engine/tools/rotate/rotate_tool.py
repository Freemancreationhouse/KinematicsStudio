from __future__ import annotations

from typing import Any

from engine.geometry import Vector3
from engine.tools.tool import Tool
from engine.transform import TransformManager

from engine.tools.rotate.rotate_context import point_to_vector3
from engine.tools.rotate.rotate_session import RotateSession


class RotateTool(Tool):
    """Professional CAD rotate tool with preview and undoable commit."""

    def __init__(self) -> None:
        """Create an inactive rotate tool."""

        super().__init__()
        self.session: RotateSession | None = None
        self.transform_manager: TransformManager | None = None
        self.entities: list[Any] = []
        self.pivot: Vector3 | None = None
        self.status_text = "Rotate: Select entities"

    def deactivate(self) -> None:
        """Cancel active rotate state when another tool is selected."""

        self.cancel()

    def mouse_press(self, workspace: Any, point: Any, additive: bool = False) -> None:
        """Select entities, choose pivot, or commit an active rotation."""

        if workspace is None:
            return

        if self.session is not None:
            self.session.update_to(point_to_vector3(point))
            self.session.commit()
            self.session = None
            self.entities = []
            self.pivot = None
            self.status_text = "Rotate: Select entities"
            return

        if not self.entities:
            self.entities = self._resolve_entities(workspace, point, additive)
            if self.entities:
                self.status_text = f"Rotate: Selected {len(self.entities)}. Select pivot"
            return

        self.pivot = point_to_vector3(point)
        self.transform_manager = getattr(workspace, "transform_manager", None)
        if self.transform_manager is None:
            self.transform_manager = TransformManager(workspace)
            workspace.transform_manager = self.transform_manager
        self.session = RotateSession(
            workspace=workspace,
            entities=self.entities,
            pivot=self.pivot,
            reference=self.pivot,
            transform_manager=self.transform_manager,
        )
        self.status_text = "Rotate: Move cursor, type angle, click to confirm"

    def mouse_move(self, workspace: Any, point: Any) -> None:
        """Update rotate preview during cursor movement."""

        if self.session is None:
            return
        self.session.update_to(point_to_vector3(point))
        self.status_text = f"Rotate: Angle {self.session.angle_degrees:.1f}"

    def mouse_release(
        self,
        workspace: Any,
        point: Any,
        additive: bool = False,
    ) -> None:
        """Leave rotation active until click confirm or numeric accept."""

    def draw_preview(self, painter: Any) -> None:
        """Draw the active rotation preview."""

        if self.session is not None:
            self.session.draw_preview(painter)

    def key_press(self, workspace: Any, key: Any) -> None:
        """Cancel on Escape or accept on Enter."""

        if key in ("Escape", "Esc", 0x01000000):
            self.cancel()
        elif key in ("Enter", "Return", 0x01000004, 0x01000005):
            self.accept()

    def set_numeric_input(self, workspace: Any, **values: Any) -> None:
        """Apply numeric rotate input and update preview before commit."""

        if self.session is None:
            selected = self._selected_entities(workspace)
            if not selected:
                return
            self.transform_manager = getattr(workspace, "transform_manager", None)
            if self.transform_manager is None:
                self.transform_manager = TransformManager(workspace)
                workspace.transform_manager = self.transform_manager
            self.entities = selected
            self.pivot = self._selection_center(selected)
            self.session = RotateSession(
                workspace=workspace,
                entities=selected,
                pivot=self.pivot,
                reference=self.pivot + Vector3(1.0, 0.0, 0.0),
                transform_manager=self.transform_manager,
            )
        self.session.set_numeric_input(**values)
        self.status_text = f"Rotate: Angle {self.session.angle_degrees:g}"

    def accept(self) -> Any:
        """Accept the active rotate session."""

        if self.session is None:
            return None
        result = self.session.commit()
        self.session = None
        self.entities = []
        self.pivot = None
        self.status_text = "Rotate: Select entities"
        return result

    def cancel(self) -> None:
        """Cancel active preview and session state."""

        if self.session is not None:
            self.session.cancel()
            self.session = None
        self.entities = []
        self.pivot = None
        self.status_text = "Rotate: Select entities"

    def _resolve_entities(
        self,
        workspace: Any,
        point: Any,
        additive: bool,
    ) -> list[Any]:
        """Resolve entities to rotate from current selection or hit testing."""

        selection = getattr(workspace, "selection", None)
        selected = self._selected_entities(workspace)
        candidates = self._selectable_entities(workspace)
        selected = [entity for entity in selected if entity in candidates]

        for entity in reversed(candidates):
            hit_test = getattr(entity, "hit_test", None)
            if callable(hit_test) and hit_test(point):
                if selected and entity in selected:
                    return selected
                if selection is not None:
                    selection.select(entity, additive)
                return [entity]

        return selected

    def _selected_entities(self, workspace: Any) -> list[Any]:
        """Return selected entities from the active selection manager."""

        selection = getattr(workspace, "selection", None)
        if selection is None:
            return []
        selected = getattr(selection, "selected", [])
        if callable(selected):
            selected = selected()
        return list(selected or [])

    def _selectable_entities(self, workspace: Any) -> list[Any]:
        """Return selectable workspace entities."""

        selectable = getattr(workspace, "selectable_entities", None)
        if callable(selectable):
            return list(selectable())
        entities = getattr(workspace, "entities", [])
        if callable(entities):
            entities = entities()
        return list(entities or [])

    def _selection_center(self, entities: list[Any]) -> Vector3:
        """Return a conservative selection center for rotate pivot fallback."""

        if not entities:
            return Vector3()

        points: list[Vector3] = []
        for entity in entities:
            for name in ("position3d", "position", "center", "start", "p1"):
                value = getattr(entity, name, None)
                if value is not None:
                    points.append(point_to_vector3(value))
                    break
        if not points:
            return Vector3()

        total = Vector3()
        for point in points:
            total = total + point
        return total / len(points)

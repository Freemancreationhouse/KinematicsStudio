from __future__ import annotations

from typing import Any

from engine.geometry import Vector3
from engine.tools.tool import Tool
from engine.transform import TransformManager

from engine.tools.move.move_context import point_to_vector3
from engine.tools.move.move_session import MoveSession


class MoveTool(Tool):
    """Professional CAD move tool with preview and undoable commit."""

    def __init__(self) -> None:
        """Create an inactive move tool."""

        super().__init__()
        self.session: MoveSession | None = None
        self.transform_manager: TransformManager | None = None

    def deactivate(self) -> None:
        """Cancel active move state when another tool is selected."""

        self.cancel()

    def mouse_press(self, workspace: Any, point: Any, additive: bool = False) -> None:
        """Start a move session from the current selection or picked entity."""

        if workspace is None:
            return

        entities = self._resolve_entities(workspace, point, additive)
        if not entities:
            return

        self.transform_manager = getattr(workspace, "transform_manager", None)
        if self.transform_manager is None:
            self.transform_manager = TransformManager(workspace)
            workspace.transform_manager = self.transform_manager

        self.session = MoveSession(
            workspace=workspace,
            entities=entities,
            start=point_to_vector3(point),
            transform_manager=self.transform_manager,
        )

    def mouse_move(self, workspace: Any, point: Any) -> None:
        """Update move preview during drag."""

        if self.session is None:
            return
        self.session.update_to(point_to_vector3(point))

    def mouse_release(
        self,
        workspace: Any,
        point: Any,
        additive: bool = False,
    ) -> None:
        """Commit the active move session."""

        if self.session is None:
            return
        self.session.update_to(point_to_vector3(point))
        self.session.commit()
        self.session = None

    def key_press(self, workspace: Any, key: Any) -> None:
        """Cancel on Escape or accept on Enter."""

        if key in ("Escape", "Esc", 0x01000000):
            self.cancel()
        elif key in ("Enter", "Return", 0x01000004, 0x01000005):
            if self.session is not None:
                self.session.commit()
                self.session = None

    def set_numeric_input(self, workspace: Any, **values: Any) -> None:
        """Apply numeric move input and update preview before commit."""

        if self.session is None:
            selected = self._selected_entities(workspace)
            if not selected:
                return
            self.transform_manager = getattr(workspace, "transform_manager", None)
            if self.transform_manager is None:
                self.transform_manager = TransformManager(workspace)
                workspace.transform_manager = self.transform_manager
            self.session = MoveSession(
                workspace=workspace,
                entities=selected,
                start=Vector3(),
                transform_manager=self.transform_manager,
            )
        self.session.set_numeric_input(**values)

    def accept(self) -> Any:
        """Accept the active move session."""

        if self.session is None:
            return None
        result = self.session.commit()
        self.session = None
        return result

    def cancel(self) -> None:
        """Cancel active preview and session state."""

        if self.session is not None:
            self.session.cancel()
            self.session = None

    def _resolve_entities(
        self,
        workspace: Any,
        point: Any,
        additive: bool,
    ) -> list[Any]:
        """Resolve entities to move from current selection or hit testing."""

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

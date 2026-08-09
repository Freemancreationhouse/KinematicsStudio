from __future__ import annotations

from typing import Any

from engine.dynamic_input import DynamicInputManager
from engine.snapping import SnappingManager
from engine.tools.entity_pick import hit_entity
from engine.tools.tool import Tool
from engine.transform import TransformManager

from engine.tools.copy.copy_context import point_to_vector3
from engine.tools.copy.copy_session import CopySession


class CopyTool(Tool):
    """Professional CAD copy tool with snapping, HUD and undoable commit."""

    def __init__(self) -> None:
        """Create an inactive copy tool."""

        super().__init__()
        self.session: CopySession | None = None
        self.transform_manager: TransformManager | None = None
        self.snapping_manager: SnappingManager | None = None
        self.dynamic_input_manager: DynamicInputManager | None = None
        self._pending_entities: list[Any] = []
        self._base_point: Any = None
        self.status_text = "Copy: Select objects"

    def deactivate(self) -> None:
        """Cancel active copy state when another tool is selected."""

        self.cancel()

    def mouse_press(self, workspace: Any, point: Any, additive: bool = False) -> None:
        """Resolve selection, base point, then commit destination point."""

        if workspace is None:
            return

        if self.session is not None:
            self.session.update_to(point_to_vector3(point))
            self.session.commit()
            self.session = None
            self.status_text = "Copy: Select objects"
            return

        if not self._pending_entities:
            self._pending_entities = self._resolve_entities(workspace, point, additive)
            if self._pending_entities:
                self.status_text = (
                    f"Copy: Selected {len(self._pending_entities)}. Pick base point"
                )
            return

        self._base_point = point_to_vector3(point)
        self._ensure_services(workspace)
        self.session = CopySession(
            workspace=workspace,
            entities=self._pending_entities,
            base_point=self._base_point,
            transform_manager=self.transform_manager,
            snapping_manager=self.snapping_manager,
            dynamic_input_manager=self.dynamic_input_manager,
        )
        self.status_text = "Copy: Pick destination point"

    def mouse_move(self, workspace: Any, point: Any) -> None:
        """Update copy preview during cursor movement."""

        if self.session is None:
            return
        self.session.update_to(point_to_vector3(point))
        self.status_text = f"Copy: Preview {self.session.copies} copy"

    def mouse_release(
        self,
        workspace: Any,
        point: Any,
        additive: bool = False,
    ) -> None:
        """Mouse release is intentionally non-committing for CAD copy workflow."""

    def draw_preview(self, painter: Any) -> None:
        """Draw transient copy preview entities."""

        if self.session is not None:
            self.session.preview.draw(painter)

    def key_press(self, workspace: Any, key: Any) -> None:
        """Cancel on Escape or accept on Enter."""

        if key in ("Escape", "Esc", 0x01000000):
            self.cancel()
        elif key in ("Enter", "Return", 0x01000004, 0x01000005):
            self.accept()

    def set_numeric_input(self, workspace: Any, **values: Any) -> None:
        """Apply Dynamic Input values and update preview before commit."""

        if self.session is None:
            selected = self._selected_entities(workspace)
            if not selected:
                return
            self._ensure_services(workspace)
            self.session = CopySession(
                workspace=workspace,
                entities=selected,
                base_point=point_to_vector3(values.pop("base_point", None)),
                transform_manager=self.transform_manager,
                snapping_manager=self.snapping_manager,
                dynamic_input_manager=self.dynamic_input_manager,
            )
        self.session.set_numeric_input(**values)
        self.status_text = f"Copy: Preview {self.session.copies} copy"

    def accept(self) -> Any:
        """Accept the active copy session."""

        if self.session is None:
            return None
        result = self.session.commit()
        self.session = None
        self._pending_entities = []
        self._base_point = None
        self.status_text = "Copy: Select objects"
        return result

    def cancel(self) -> None:
        """Cancel active preview and session state."""

        if self.session is not None:
            self.session.cancel()
            self.session = None
        self._pending_entities = []
        self._base_point = None
        self.status_text = "Copy: Select objects"

    def _ensure_services(self, workspace: Any) -> None:
        """Resolve shared services without owning locked systems."""

        self.transform_manager = getattr(workspace, "transform_manager", None)
        if self.transform_manager is None:
            self.transform_manager = TransformManager(workspace)
            workspace.transform_manager = self.transform_manager

        self.snapping_manager = getattr(workspace, "snapping_manager", None)
        if self.snapping_manager is None:
            self.snapping_manager = getattr(workspace, "snap_manager", None)
        if self.snapping_manager is None:
            self.snapping_manager = SnappingManager()
            workspace.snapping_manager = self.snapping_manager

        self.dynamic_input_manager = getattr(workspace, "dynamic_input_manager", None)
        if self.dynamic_input_manager is None:
            self.dynamic_input_manager = DynamicInputManager()
            workspace.dynamic_input_manager = self.dynamic_input_manager

    def _resolve_entities(
        self,
        workspace: Any,
        point: Any,
        additive: bool,
    ) -> list[Any]:
        """Resolve entities to copy from current selection or hit testing."""

        selection = getattr(workspace, "selection", None)
        selected = self._selected_entities(workspace)
        hit = hit_entity(workspace, point)

        if hit is not None:
            if selection is not None:
                selection.select(hit, additive)
            if selected and hit in selected:
                return selected
            if additive and selected:
                return self._selected_entities(workspace)
            return [hit]

        return selected

    def _selected_entities(self, workspace: Any) -> list[Any]:
        """Return selected entities from the active selection manager."""

        if workspace is None:
            return []
        selection = getattr(workspace, "selection", None)
        if selection is None:
            return []
        selected = getattr(selection, "selected", [])
        if callable(selected):
            selected = selected()
        return list(selected or [])

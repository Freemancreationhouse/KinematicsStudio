from time import perf_counter

from engine.workspace import WorkspaceManager
from engine.tools import ToolManager
from engine.render import (
    Camera,
    Camera3D,
    Renderer,
    Renderer3D,
    ViewTransform,
)
from engine.input import InputManager
from engine.snap import SnapManager
from engine.ai import AIEngine

from engine.cad.occ_manager import OCCManager
from engine.cad.occ_importer import OCCImporter
from engine.cad.occ_exporter import OCCExporter
from engine.cad.occ_boolean import OCCBoolean
from engine.cad.occ_mesher import OCCMesher
from engine.cad.occ_selection import OCCSelection
from engine.cad.occ_history import OCCHistory


class CADEngine:
    """Coordinates workspace, tools, rendering, commands, input, snapping, and OpenCascade."""

    def __init__(self):

        startup_started = perf_counter()

        self.workspace_manager = WorkspaceManager()

        self.workspace = self.workspace_manager.create("Model")

        self.tool_manager = ToolManager()

        self.renderer = Renderer()

        self.camera = Camera()

        self.renderer.camera = self.camera

        self.renderer3d = Renderer3D()
        self.renderer3d.cad_engine = self

        self.camera3d = Camera3D()

        self.renderer3d.camera = self.camera3d

        self.view = ViewTransform(self.camera)

        self.input = InputManager()

        self.snap_manager = SnapManager()

        self.ai_engine = AIEngine()

        # =================================================
        # OpenCascade
        # =================================================

        self.occ = OCCManager()

        self.occ_importer = OCCImporter()

        self.occ_exporter = OCCExporter()

        self.occ_boolean = OCCBoolean()

        self.occ_mesher = OCCMesher()

        self.occ_selection = OCCSelection()

        self.occ_history = OCCHistory()
        self.workspace.selection.bind_occ_selection(self.occ, self.occ_selection)
        self.runtime_started_at = startup_started
        self.runtime_initialized_at = perf_counter()
        self.update_count = 0
        self.runtime_validation = self.validate_runtime()
        self.runtime_diagnostics = self.diagnostics()

    # -------------------------------------------------

    def update(self):
        self.update_count += 1
        self.runtime_diagnostics = self.diagnostics()
        return self.runtime_diagnostics

    # -------------------------------------------------

    def set_workspace(self, workspace):
        """Replace the active workspace while preserving engine services."""

        self.workspace = workspace

        self.workspace_manager.workspaces[workspace.name] = workspace

        self.workspace_manager.active = workspace
        self.occ_selection.clear()
        self.workspace.selection.bind_occ_selection(self.occ, self.occ_selection)
        self.runtime_validation = self.validate_runtime()
        self.runtime_diagnostics = self.diagnostics()

        return workspace

    # -------------------------------------------------

    def reset_workspace(self, name="Model"):
        """Create and activate a clean workspace through the existing runtime."""

        if self.workspace is not None:
            self.workspace.clear()
        workspace = self.workspace_manager.create(name)
        self.set_workspace(workspace)
        return workspace

    # -------------------------------------------------

    def dispose_workspace(self, workspace=None):
        """Dispose workspace-owned state without creating duplicate runtime systems."""

        target = workspace or self.workspace
        if target is None:
            return None

        target.clear()
        if target.name in self.workspace_manager.workspaces:
            self.workspace_manager.remove(target.name)
        self.occ.clear()
        self.occ_selection.clear()
        self.occ_history.clear()
        self.runtime_validation = self.validate_runtime()
        self.runtime_diagnostics = self.diagnostics()
        return target

    # -------------------------------------------------

    def validate_runtime(self):
        """Return production runtime registration and ownership validation metadata."""

        workspace = self.workspace
        product = getattr(workspace, "product_manager", None)
        checks = {
            "workspace_initialized": workspace is not None,
            "workspace_manager_active": self.workspace_manager.active is workspace,
            "selection_initialized": getattr(workspace, "selection", None) is not None,
            "command_manager_initialized": getattr(workspace, "command_manager", None) is not None,
            "renderer2d_initialized": self.renderer is not None and getattr(self.renderer, "camera", None) is self.camera,
            "renderer3d_initialized": self.renderer3d is not None and getattr(self.renderer3d, "camera", None) is self.camera3d,
            "renderer3d_cad_engine_bound": getattr(self.renderer3d, "cad_engine", None) is self,
            "product_manager_initialized": product is not None,
            "dependency_manager_initialized": getattr(product, "dependency_manager", None) is not None if product is not None else False,
            "feature_manager_initialized": getattr(product, "feature_manager", None) is not None if product is not None else False,
            "body_manager_initialized": getattr(product, "body_manager", None) is not None if product is not None else False,
            "geometry_kernel_path_initialized": getattr(product, "parametric_manager", None) is not None if product is not None else False,
            "update_manager_initialized": getattr(product, "update_manager", None) is not None if product is not None else False,
            "ai_runtime_initialized": self.ai_engine is not None,
            "occ_runtime_initialized": all([
                self.occ is not None,
                self.occ_importer is not None,
                self.occ_exporter is not None,
                self.occ_boolean is not None,
                self.occ_mesher is not None,
                self.occ_selection is not None,
                self.occ_history is not None,
            ]),
            "single_active_workspace": list(self.workspace_manager.workspaces.values()).count(workspace) == 1,
        }
        checks["production_ready"] = all(checks.values())
        return checks

    # -------------------------------------------------

    def diagnostics(self):
        """Return production runtime diagnostics using existing subsystem statistics."""

        workspace = self.workspace
        product = getattr(workspace, "product_manager", None)
        scene = getattr(workspace, "scene3d", None)
        command_manager = getattr(workspace, "command_manager", None)
        selection = getattr(workspace, "selection", None)
        diagnostics = {
            "startup_time_ms": round(max(self.runtime_initialized_at - self.runtime_started_at, 0.0) * 1000.0, 3) if hasattr(self, "runtime_initialized_at") else 0.0,
            "updates": self.update_count,
            "workspaces": len(self.workspace_manager.workspaces),
            "active_workspace": getattr(workspace, "name", ""),
            "entities_2d": len(getattr(workspace, "entities", [])),
            "entities_3d": len(scene.entities()) if scene is not None else 0,
            "selection_count": len(getattr(selection, "selected", [])) if selection is not None else 0,
            "undo_count": getattr(command_manager, "undo_count", 0) if command_manager is not None else 0,
            "redo_count": getattr(command_manager, "redo_count", 0) if command_manager is not None else 0,
            "occ_shapes": len(getattr(self.occ, "shapes", [])),
            "occ_selected": len(getattr(self.occ_selection, "selected", [])),
            "occ_undo": getattr(self.occ_history, "undo_count", 0),
            "occ_redo": getattr(self.occ_history, "redo_count", 0),
            "runtime_validation": dict(getattr(self, "runtime_validation", {}) or {}),
            "ai": self.ai_engine.diagnostics(),
        }
        if product is not None:
            diagnostics.update({
                "documents": len(getattr(product, "documents", [])),
                "parts": len(getattr(product, "parts", [])),
                "features": len(getattr(product, "features", [])),
                "bodies": len(getattr(product, "bodies", [])),
                "dependency_nodes": len(getattr(product, "dependency_nodes", [])),
                "dependency_edges": len(getattr(product, "dependency_edges", [])),
                "dirty_features": len([
                    state for state in getattr(product, "feature_states", {}).values()
                    if getattr(state, "dirty", False)
                ]),
                "geometry_kernels": len(getattr(product, "geometry_kernels", [])),
                "geometry_results": len(getattr(product, "geometry_results", [])),
                "execution_engines": len(getattr(product, "execution_engines", [])),
                "execution_results": len(getattr(product, "execution_results", [])),
            })
        return diagnostics

    # -------------------------------------------------

    def render(
        self,
        painter,
        width,
        height,
        snap_result=None,
    ):

        self.renderer.render(
            painter,
            self.workspace,
            self.tool_manager.current,
            width,
            height,
            snap_result,
        )

    # -------------------------------------------------

    def render3d(
        self,
        painter,
        width,
        height,
    ):

        self.renderer3d.render(
            painter,
            self.workspace,
            width,
            height,
        )

    # =================================================
    # OCC Shape Management
    # =================================================

    def clear_shapes(self):

        self.occ.clear()

    # -------------------------------------------------

    def add_shape(self, shape):

        return self.occ.add(shape)

    # -------------------------------------------------

    def get_shapes(self):

        return self.occ.shapes

    # -------------------------------------------------

    def shape_count(self):

        return len(self.occ.shapes)

    # =================================================
    # Primitive Creation
    # =================================================

    def create_box(
        self,
        width=100,
        depth=100,
        height=100,
    ):

        return self.occ.box(
            width,
            depth,
            height,
        )

    # -------------------------------------------------

    def create_cylinder(
        self,
        radius=50,
        height=100,
    ):

        return self.occ.cylinder(
            radius,
            height,
        )

    # -------------------------------------------------

    def create_sphere(
        self,
        radius=50,
    ):

        return self.occ.sphere(
            radius,
        )

    # =================================================
    # Import / Export
    # =================================================

    def import_model(self, filename):

        self.occ_history.save(self.occ)

        return self.occ_importer.import_into_manager(
            filename,
            self.occ,
        )

    # -------------------------------------------------

    def export_model(self, filename):

        return self.occ_exporter.export_manager(
            self.occ,
            filename,
        )

    # =================================================
    # Boolean Operations
    # =================================================

    def boolean_union(
        self,
        shape_a,
        shape_b,
    ):

        self.occ_history.save(self.occ)

        return self.occ_boolean.replace(
            self.occ,
            shape_a,
            shape_b,
            "union",
        )

    # -------------------------------------------------

    def boolean_subtract(
        self,
        shape_a,
        shape_b,
    ):

        self.occ_history.save(self.occ)

        return self.occ_boolean.replace(
            self.occ,
            shape_a,
            shape_b,
            "subtract",
        )

    # -------------------------------------------------

    def boolean_intersect(
        self,
        shape_a,
        shape_b,
    ):

        self.occ_history.save(self.occ)

        return self.occ_boolean.replace(
            self.occ,
            shape_a,
            shape_b,
            "intersect",
        )

    # =================================================
    # Meshing
    # =================================================

    def mesh_shape(self, shape):

        return self.occ_mesher.triangulation(shape)

    # -------------------------------------------------

    def mesh_all_shapes(self):

        return self.occ_mesher.mesh_manager(
            self.occ,
        )

    # =================================================
    # Selection
    # =================================================

    def select_shape(
        self,
        shape,
        additive=False,
    ):

        self.occ_selection.select(
            shape,
            additive,
        )

    # -------------------------------------------------

    def clear_selection(self):

        self.occ_selection.clear()

    # -------------------------------------------------

    def selected_shapes(self):

        return self.occ_selection.selected

    # =================================================
    # Undo / Redo
    # =================================================

    def undo(self):

        return self.occ_history.undo(
            self.occ,
        )

    # -------------------------------------------------

    def redo(self):

        return self.occ_history.redo(
            self.occ,
        )

    # -------------------------------------------------

    def save_history(self):

        self.occ_history.save(
            self.occ,
        )

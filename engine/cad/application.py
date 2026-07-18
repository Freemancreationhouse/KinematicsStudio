from datetime import datetime, timezone

from engine.cad import CADEngine
from engine.storage import (
    AutoSaveManager,
    PROJECT_FORMAT_VERSION,
    ProjectSerializer,
    ProjectTemplateManager,
    RecentFilesManager,
)
from engine.export import ExportManager


class CADApplication:
    """Facade used by the UI to access the CAD engine."""

    def __init__(self):

        self.engine = CADEngine()
        self.project_serializer = ProjectSerializer()
        self.export_manager = ExportManager()
        self.project_templates = ProjectTemplateManager()
        self.recent_files = RecentFilesManager()
        self.project_path = None
        self.last_save_time = None
        self.autosave = AutoSaveManager(
            lambda: self.workspace,
            serializer=self.project_serializer,
        )

    # --------------------------------

    def update(self):

        self.engine.update()

    # --------------------------------

    def render(self, painter, width, height, snap_result=None):

        self.engine.render(

            painter,

            width,

            height,

            snap_result

        )

    # --------------------------------

    def render3d(self, painter, width, height):
        """Render the 3D foundation viewport."""

        self.engine.render3d(painter, width, height)

    # --------------------------------

    def save_project(self, path=None):
        """Save the active workspace to a project file."""

        target = path or self.project_path

        if target is None:
            raise ValueError("Project path is required")

        saved = self.project_serializer.save(
            self.workspace,
            target,
            settings=self._project_settings(),
        )
        self.project_path = str(saved)
        self.last_save_time = self._timestamp()
        self.recent_files.add(saved)
        self.autosave.clear_recovery()

        return saved

    # --------------------------------

    def open_project(self, path):
        """Load a project file and replace the active workspace."""

        workspace = self.project_serializer.load(path)
        self.engine.set_workspace(workspace)
        self._restore_project_settings(workspace.project_settings)
        self.project_path = str(path)
        self.last_save_time = None
        self.recent_files.add(path)

        return workspace

    # --------------------------------

    def new_project(self, template_name=None):
        """Create a new workspace from a registered project template."""

        workspace = self.project_templates.create_workspace(
            template_name or ProjectTemplateManager.BLANK
        )
        self.engine.set_workspace(workspace)
        self.camera3d.home_view()
        self.project_path = None
        self.last_save_time = None

        return workspace

    # --------------------------------

    def project_info(self):
        """Return current project metadata for UI display."""

        workspace = self.workspace

        return {
            "current_project": workspace.name,
            "file_path": self.project_path or "Unsaved",
            "version": str(PROJECT_FORMAT_VERSION),
            "last_save_time": self.last_save_time or "Not saved",
            "autosave_status": "On" if self.autosave.enabled else "Off",
            "entity_count": len(workspace.entities),
            "layer_count": getattr(workspace.layer_manager, "count", 0),
            "block_count": getattr(workspace.block_manager, "count", 0),
            "group_count": getattr(workspace.group_manager, "count", 0),
        }

    # --------------------------------

    def export_project(self, path, format_name=None, options=None):
        """Export the active workspace through the shared export framework."""

        return self.export_manager.export(
            self.workspace,
            path,
            format_name=format_name,
            options=options,
        )

    # --------------------------------

    def autosave_now(self):
        """Write the active workspace to the configured recovery file."""

        return self.autosave.autosave_now()

    # --------------------------------

    def has_recovery(self):
        """Return True when a recovery file exists."""

        return self.autosave.has_recovery()

    # --------------------------------

    def recover_project(self):
        """Load the autosave recovery workspace if available."""

        workspace = self.autosave.load_recovery()

        if workspace is not None:
            self.engine.set_workspace(workspace)
            self._restore_project_settings(workspace.project_settings)
            self.project_path = None
            self.last_save_time = None

        return workspace

    # --------------------------------

    @property
    def workspace(self):

        return self.engine.workspace

    # --------------------------------

    @property
    def tool_manager(self):

        return self.engine.tool_manager

    # --------------------------------

    @property
    def camera(self):

        return self.engine.camera

    # --------------------------------

    @property
    def camera3d(self):

        return self.engine.camera3d

    # --------------------------------

    @property
    def snap_manager(self):

        return self.engine.snap_manager

    # --------------------------------

    def _project_settings(self):

        settings = dict(getattr(self.workspace, "project_settings", {}) or {})
        settings["view3d"] = {
            "camera": self.camera3d.to_dict(),
            "viewport": {
                "mode": "3d-ready",
            },
        }
        self.workspace.project_settings = settings

        return settings

    # --------------------------------

    def _restore_project_settings(self, settings):

        view3d = dict((settings or {}).get("view3d", {}))
        self.camera3d.from_dict(view3d.get("camera", {}))

    # --------------------------------

    def _timestamp(self):

        return datetime.now(timezone.utc).isoformat()

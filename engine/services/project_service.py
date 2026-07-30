from __future__ import annotations

from collections.abc import Iterable
from os import PathLike
from pathlib import Path
from typing import Any


class ProjectService:
    """Authoritative UI-free API for project-level operations."""

    def __init__(self, workspace: Any) -> None:
        """Create a project service for an existing workspace-like object."""

        self._workspace = self._resolve_workspace(workspace)
        self._project_api = workspace
        self._project_path: str | None = self._read_project_path(workspace)
        self._metadata: dict[str, Any] = {}
        self._recent_files: list[str] = []
        self._autosave_enabled = self._read_autosave_enabled(workspace)
        self._dirty = False

    def new_project(self) -> Any:
        """Create a new project through the existing project API when present."""

        project_api = self._project_api
        result = self._call_first(project_api, ("new_project", "create_project"))
        if result is not None:
            self._workspace = self._resolve_workspace(result)
        elif self._call_first(self._workspace, ("clear",)) is not None:
            result = self._workspace

        self._project_path = self._read_project_path(project_api)
        self.clear_dirty()
        return result

    def open_project(self, path: str | PathLike[str]) -> Any:
        """Open a project through the existing project API when available."""

        normalized = self._normalize_path(path)
        project_api = self._project_api
        result = self._call_first(
            project_api,
            ("open_project", "load_project", "open", "load"),
            normalized,
        )
        if result is not None:
            self._workspace = self._resolve_workspace(result)
            self.set_project_path(normalized)
            self.add_recent_file(normalized)
            self.clear_dirty()
        return result

    def save(self) -> Any:
        """Save the current project using the existing project API."""

        project_api = self._project_api
        result = self._call_first(project_api, ("save_project", "save"))
        if result is not None:
            self.set_project_path(result)
            self.add_recent_file(result)
            self.clear_dirty()
        return result

    def save_as(self, path: str | PathLike[str]) -> Any:
        """Save the current project to a new path using existing storage."""

        normalized = self._normalize_path(path)
        project_api = self._project_api
        result = self._call_first(
            project_api,
            ("save_project", "save_as", "save"),
            normalized,
        )
        if result is not None:
            self.set_project_path(result)
            self.add_recent_file(result)
            self.clear_dirty()
        return result

    def close_project(self) -> Any:
        """Close the active project through existing project APIs."""

        project_api = self._project_api
        result = self._call_first(project_api, ("close_project", "close"))
        if result is not None:
            self._workspace = self._resolve_workspace(result)
        elif self._call_first(self._workspace, ("clear",)) is not None:
            result = self._workspace

        self._project_path = None
        self.clear_dirty()
        return result

    def reload(self) -> Any:
        """Reload the current project from its known project path."""

        path = self.project_path()
        if path is None:
            return None
        return self.open_project(path)

    def is_dirty(self) -> bool:
        """Return True when the project has unsaved changes."""

        value = self._read_attr_or_call(
            self._project_api,
            ("is_dirty", "dirty", "has_unsaved_changes"),
        )
        if value is None:
            value = self._read_attr_or_call(
                self._workspace,
                ("is_dirty", "dirty", "has_unsaved_changes"),
            )
        return bool(self._dirty if value is None else value)

    def mark_dirty(self) -> None:
        """Mark the current project as dirty."""

        if not self._call_optional(self._project_api, "mark_dirty"):
            self._call_optional(self._workspace, "mark_dirty")
        self._dirty = True

    def clear_dirty(self) -> None:
        """Clear the dirty state after save, open, close, or reload."""

        if not self._call_optional(self._project_api, "clear_dirty"):
            self._call_optional(self._workspace, "clear_dirty")
        self._dirty = False

    def project_name(self) -> str:
        """Return the current project name."""

        value = self._read_attr_or_call(
            self._project_api,
            ("project_name", "name"),
        )
        if value is None:
            value = self._read_attr_or_call(self._workspace, ("project_name", "name"))
        if value:
            return str(value)
        path = self.project_path()
        return Path(path).stem if path else "Untitled"

    def project_path(self) -> str | None:
        """Return the current project path when known."""

        value = self._read_project_path(self._project_api)
        if value is not None:
            self._project_path = value
        return self._project_path

    def set_project_path(self, path: str | PathLike[str] | None) -> None:
        """Set the current project path on this service and existing APIs."""

        normalized = None if path is None else self._normalize_path(path)
        self._project_path = normalized
        self._write_attr_if_present(self._project_api, "project_path", normalized)
        self._write_attr_if_present(self._workspace, "project_path", normalized)

    def workspace(self) -> Any:
        """Return the current workspace reference."""

        return self._resolve_workspace(self._project_api) or self._workspace

    def metadata(self) -> dict[str, Any]:
        """Return mutable project metadata from the workspace when available."""

        settings = getattr(self.workspace(), "project_settings", None)
        if isinstance(settings, dict):
            return settings
        metadata = getattr(self.workspace(), "metadata", None)
        if isinstance(metadata, dict):
            return metadata
        return self._metadata

    def set_metadata(self, key: str, value: Any) -> None:
        """Set one project metadata value."""

        self.metadata()[key] = value
        self.mark_dirty()

    def recent_files(self) -> list[str]:
        """Return known recent project file paths."""

        recent_owner = getattr(self._project_api, "recent_files", None)
        values = self._extract_recent_files(recent_owner)
        if values is None:
            values = self._extract_recent_files(self._project_api)
        return list(self._recent_files if values is None else values)

    def add_recent_file(self, path: str | PathLike[str]) -> None:
        """Add a project path to the recent-files list."""

        normalized = self._normalize_path(path)
        recent_owner = getattr(self._project_api, "recent_files", None)
        if not self._call_optional(recent_owner, "add", normalized):
            if normalized in self._recent_files:
                self._recent_files.remove(normalized)
            self._recent_files.insert(0, normalized)

    def clear_recent_files(self) -> None:
        """Clear recent files through the existing owner when possible."""

        recent_owner = getattr(self._project_api, "recent_files", None)
        if not self._call_optional(recent_owner, "clear"):
            self._recent_files.clear()

    def autosave_enabled(self) -> bool:
        """Return True when autosave is enabled."""

        autosave = getattr(self._project_api, "autosave", None)
        value = self._read_attr_or_call(autosave, ("enabled", "is_enabled"))
        if value is None:
            value = self._read_attr_or_call(
                self._project_api,
                ("autosave_enabled",),
            )
        return bool(self._autosave_enabled if value is None else value)

    def set_autosave_enabled(self, enabled: bool) -> None:
        """Enable or disable autosave using the existing autosave owner."""

        autosave = getattr(self._project_api, "autosave", None)
        if enabled:
            changed = self._call_optional(autosave, "start")
        else:
            changed = self._call_optional(autosave, "stop")
        if not changed:
            self._write_attr_if_present(autosave, "enabled", enabled)
            self._call_optional(self._project_api, "set_autosave_enabled", enabled)
        self._autosave_enabled = enabled

    def undo(self) -> Any:
        """Undo the latest command through the existing command manager."""

        command_manager = self._command_manager()
        return self._call_first(command_manager, ("undo",))

    def redo(self) -> Any:
        """Redo the latest command through the existing command manager."""

        command_manager = self._command_manager()
        return self._call_first(command_manager, ("redo",))

    def can_undo(self) -> bool:
        """Return True when undo is available."""

        command_manager = self._command_manager()
        value = self._read_attr_or_call(
            command_manager,
            ("can_undo", "undo_available"),
        )
        return bool(value)

    def can_redo(self) -> bool:
        """Return True when redo is available."""

        command_manager = self._command_manager()
        value = self._read_attr_or_call(
            command_manager,
            ("can_redo", "redo_available"),
        )
        return bool(value)

    def _command_manager(self) -> Any:
        """Return the command manager from the active workspace."""

        return getattr(self.workspace(), "command_manager", None)

    def _resolve_workspace(self, obj: Any) -> Any:
        """Resolve a workspace from an object or return the object itself."""

        workspace = getattr(obj, "workspace", None)
        if workspace is not None and workspace is not obj:
            return workspace
        return obj

    def _read_project_path(self, obj: Any) -> str | None:
        """Read a project path from an object when available."""

        value = self._read_attr_or_call(
            obj,
            ("project_path", "path", "file_path"),
        )
        if value in (None, "", "Unsaved"):
            return None
        return self._normalize_path(value)

    def _read_autosave_enabled(self, obj: Any) -> bool:
        """Read the initial autosave state from available objects."""

        autosave = getattr(obj, "autosave", None)
        value = self._read_attr_or_call(autosave, ("enabled", "is_enabled"))
        return bool(value) if value is not None else False

    def _extract_recent_files(self, obj: Any) -> list[str] | None:
        """Extract recent files from common existing recent-file owners."""

        if obj is None:
            return None
        for name in ("files", "paths", "recent_files"):
            value = getattr(obj, name, None)
            if callable(value):
                value = value()
            if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
                return [self._normalize_path(item) for item in value]
        if isinstance(obj, Iterable) and not isinstance(obj, (str, bytes)):
            return [self._normalize_path(item) for item in obj]
        return None

    def _call_first(self, obj: Any, names: tuple[str, ...], *args: Any) -> Any:
        """Call the first available method from a list of method names."""

        if obj is None:
            return None
        for name in names:
            method = getattr(obj, name, None)
            if callable(method):
                return method(*args)
        return None

    def _call_optional(self, obj: Any, name: str, *args: Any) -> bool:
        """Call an optional method and report whether it existed."""

        method = getattr(obj, name, None)
        if not callable(method):
            return False
        method(*args)
        return True

    def _read_attr_or_call(self, obj: Any, names: tuple[str, ...]) -> Any:
        """Read the first available attribute or zero-argument method."""

        if obj is None:
            return None
        for name in names:
            if not hasattr(obj, name):
                continue
            value = getattr(obj, name)
            if callable(value):
                try:
                    return value()
                except TypeError:
                    continue
            return value
        return None

    def _write_attr_if_present(self, obj: Any, name: str, value: Any) -> bool:
        """Write an attribute only when the object already exposes it."""

        if obj is None or not hasattr(obj, name):
            return False
        setattr(obj, name, value)
        return True

    def _normalize_path(self, path: Any) -> str:
        """Return a normalized string path."""

        return str(Path(path))

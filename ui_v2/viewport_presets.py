from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QSettings


@dataclass(frozen=True)
class ViewportPreset:
    """UI-only viewport preset definition."""

    preset_id: str
    name: str
    state: dict[str, Any]
    built_in: bool = False


@dataclass(frozen=True)
class WorkspaceProfile:
    """Workspace profile that applies a viewport preset without project data."""

    profile_id: str
    name: str
    preset_id: str


class ViewportPresetManager:
    """Persist and apply viewport presets and workspace profiles."""

    BUILT_IN_PRESETS = (
        ("single_view", "Single View"),
        ("drafting", "Drafting"),
        ("modeling", "Modeling"),
        ("quad_view", "Quad View"),
        ("presentation", "Presentation"),
        ("visualization", "Visualization"),
    )
    WORKSPACE_PROFILES = (
        ("architecture", "Architecture", "drafting"),
        ("mechanical", "Mechanical", "quad_view"),
        ("product_design", "Product Design", "modeling"),
        ("visualization", "Visualization", "visualization"),
        ("cam", "CAM", "modeling"),
        ("digital_fabrication", "Digital Fabrication", "modeling"),
        ("robotics", "Robotics", "quad_view"),
    )

    def __init__(self, viewport_area: Any) -> None:
        """Create a preset manager for an injected viewport area."""

        self._viewport_area = viewport_area
        self._settings = QSettings("Freeman Creations House", "Kinematics Studio")
        self._custom_presets: dict[str, ViewportPreset] = {}
        self._load_custom_presets()

    def presets(self) -> tuple[ViewportPreset, ...]:
        """Return all built-in and custom presets."""

        return self.built_in_presets() + tuple(self._custom_presets.values())

    def built_in_presets(self) -> tuple[ViewportPreset, ...]:
        """Return deterministic built-in presets."""

        presets = []
        for preset_id, name in self.BUILT_IN_PRESETS:
            presets.append(
                ViewportPreset(
                    preset_id=preset_id,
                    name=name,
                    state=self._default_state(preset_id),
                    built_in=True,
                )
            )
        return tuple(presets)

    def custom_presets(self) -> tuple[ViewportPreset, ...]:
        """Return user-saved custom presets."""

        return tuple(self._custom_presets.values())

    def profiles(self) -> tuple[WorkspaceProfile, ...]:
        """Return built-in workspace profiles."""

        return tuple(
            WorkspaceProfile(profile_id, name, preset_id)
            for profile_id, name, preset_id in self.WORKSPACE_PROFILES
        )

    def preset(self, preset_id: str) -> ViewportPreset | None:
        """Return one preset by id."""

        for item in self.built_in_presets():
            if item.preset_id == preset_id:
                return item
        return self._custom_presets.get(preset_id)

    def profile(self, profile_id: str) -> WorkspaceProfile | None:
        """Return one workspace profile by id."""

        for item in self.profiles():
            if item.profile_id == profile_id:
                return item
        return None

    def apply_preset(self, preset_id: str) -> bool:
        """Apply a viewport preset without touching project data."""

        preset = self.preset(preset_id)
        if preset is None:
            return False
        apply_state = getattr(self._viewport_area, "apply_workspace_preset_state", None)
        if not callable(apply_state):
            return False
        apply_state(dict(preset.state))
        self._settings.setValue("viewport_presets/active_preset", preset_id)
        return True

    def apply_profile(self, profile_id: str) -> bool:
        """Apply a workspace profile without touching project data."""

        profile = self.profile(profile_id)
        if profile is None:
            return False
        if not self.apply_preset(profile.preset_id):
            return False
        self._settings.setValue("viewport_presets/active_profile", profile_id)
        return True

    def save_current(self, name: str) -> ViewportPreset:
        """Save the current viewport state as a custom preset."""

        clean_name = self._clean_name(name)
        preset_id = self._custom_id(clean_name)
        capture = getattr(self._viewport_area, "capture_workspace_preset_state", None)
        state = capture() if callable(capture) else {}
        preset = ViewportPreset(
            preset_id=preset_id,
            name=clean_name,
            state=state,
            built_in=False,
        )
        self._custom_presets[preset_id] = preset
        self._save_custom_presets()
        return preset

    def rename_preset(self, preset_id: str, name: str) -> bool:
        """Rename a custom preset."""

        if preset_id not in self._custom_presets:
            return False
        preset = self._custom_presets[preset_id]
        self._custom_presets[preset_id] = ViewportPreset(
            preset_id=preset.preset_id,
            name=self._clean_name(name),
            state=preset.state,
            built_in=False,
        )
        self._save_custom_presets()
        return True

    def delete_preset(self, preset_id: str) -> bool:
        """Delete a custom preset."""

        if preset_id not in self._custom_presets:
            return False
        self._custom_presets.pop(preset_id, None)
        self._save_custom_presets()
        return True

    def restore_default_presets(self) -> None:
        """Remove custom presets and restore built-in preset availability."""

        self._custom_presets.clear()
        self._save_custom_presets()
        self._settings.remove("viewport_presets/active_preset")
        self._settings.remove("viewport_presets/active_profile")

    def restore_last_preset(self) -> bool:
        """Restore the last active preset when available."""

        preset_id = self._settings.value("viewport_presets/active_preset")
        if preset_id:
            return self.apply_preset(str(preset_id))
        return False

    def _default_state(self, preset_id: str) -> dict[str, Any]:
        """Return a built-in preset state from the viewport area."""

        method = getattr(self._viewport_area, "default_workspace_preset_state", None)
        return method(preset_id) if callable(method) else {}

    def _load_custom_presets(self) -> None:
        """Load custom presets from QSettings."""

        encoded = self._settings.value("viewport_presets/custom")
        if not encoded:
            return
        try:
            records = json.loads(str(encoded))
        except (TypeError, ValueError):
            return
        if not isinstance(records, list):
            return
        for record in records:
            if not isinstance(record, dict):
                continue
            preset_id = str(record.get("preset_id", "")).strip()
            name = str(record.get("name", "")).strip()
            state = record.get("state", {})
            if not preset_id or not name or not isinstance(state, dict):
                continue
            self._custom_presets[preset_id] = ViewportPreset(
                preset_id=preset_id,
                name=name,
                state=state,
                built_in=False,
            )

    def _save_custom_presets(self) -> None:
        """Persist custom presets to QSettings."""

        records = [
            {
                "preset_id": preset.preset_id,
                "name": preset.name,
                "state": preset.state,
            }
            for preset in self._custom_presets.values()
        ]
        self._settings.setValue("viewport_presets/custom", json.dumps(records))

    def _custom_id(self, name: str) -> str:
        """Create a stable unique custom preset id."""

        base = "".join(
            character.lower() if character.isalnum() else "_"
            for character in name
        ).strip("_") or "workspace_preset"
        preset_id = f"custom_{base}"
        if preset_id not in self._custom_presets:
            return preset_id
        index = 2
        while f"{preset_id}_{index}" in self._custom_presets:
            index += 1
        return f"{preset_id}_{index}"

    def _clean_name(self, name: str) -> str:
        """Return a display-safe preset name."""

        clean = str(name).strip()
        if not clean:
            raise ValueError("Preset name must not be empty.")
        return clean

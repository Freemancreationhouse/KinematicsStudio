from engine.render import Camera3DState


DISPLAY_MODES = (
    "wireframe",
    "hidden_line",
    "shaded",
    "shaded_with_edges",
    "x_ray",
    "bounding_box",
    "analysis_overlay",
)


class ViewState:
    """Named 3D view state with camera and display metadata."""

    def __init__(self, name="View", camera=None, display_mode="wireframe", visual_style="Default"):

        self.name = str(name)
        self.camera = Camera3DState.from_dict(camera or {})
        self.display_mode = _normalize_display_mode(display_mode)
        self.visual_style = visual_style or "Default"

    # --------------------------------

    @staticmethod
    def from_camera(name, camera, display_mode="wireframe", visual_style="Default"):
        """Create a view state from a Camera3D instance."""

        return ViewState(
            name,
            camera.to_dict() if camera is not None else {},
            display_mode,
            visual_style,
        )

    # --------------------------------

    def apply_to_camera(self, camera):
        """Restore this view state onto a Camera3D instance."""

        if camera is not None:
            camera.from_dict(self.camera.to_dict())

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe view state data."""

        return {
            "name": self.name,
            "camera": self.camera.to_dict(),
            "display_mode": self.display_mode,
            "visual_style": self.visual_style,
        }

    # --------------------------------

    @staticmethod
    def from_dict(data):
        """Create a view state from persisted data."""

        data = data or {}

        return ViewState(
            data.get("name", "View"),
            data.get("camera", {}),
            data.get("display_mode", "wireframe"),
            data.get("visual_style", "Default"),
        )


class ViewStateManager:
    """Workspace-owned manager for current and named 3D views."""

    def __init__(self):

        self.views = []
        self.current = None

    # --------------------------------

    def save_view(self, name, camera, display_mode="wireframe", visual_style="Default"):
        """Save or replace a named view from camera state."""

        existing = self.get(name)
        view = ViewState.from_camera(
            name,
            camera,
            display_mode,
            visual_style,
        )

        if existing is not None:
            index = self.views.index(existing)
            view.name = existing.name
            self.views[index] = view
        else:
            view.name = self._unique_name(name)
            self.views.append(view)

        self.current = view

        return view

    # --------------------------------

    def add(self, view):
        """Store a named view."""

        if view not in self.views:
            view.name = self._unique_name(view.name, view)
            self.views.append(view)

        if self.current is None:
            self.current = view

        return view

    # --------------------------------

    def restore_view(self, view, camera):
        """Restore a named view to a Camera3D instance."""

        target = self.get(view)

        if target is None:
            return None

        target.apply_to_camera(camera)
        self.current = target

        return target

    # --------------------------------

    def rename(self, view, new_name):
        """Rename a named view."""

        target = self.get(view)

        if target is None:
            return False

        target.name = self._unique_name(new_name, target)

        return True

    # --------------------------------

    def delete(self, view):
        """Delete a named view."""

        target = self.get(view)

        if target is None:
            return False

        self.views.remove(target)

        if self.current is target:
            self.current = self.views[0] if self.views else None

        return True

    # --------------------------------

    def get(self, view):
        """Return view by object or name."""

        if isinstance(view, ViewState):
            return view if view in self.views else None

        for item in self.views:
            if item.name == view:
                return item

        return None

    # --------------------------------

    def names(self):
        """Return named view names."""

        return [view.name for view in self.views]

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe view manager data."""

        return {
            "current": getattr(self.current, "name", None),
            "views": [view.to_dict() for view in self.views],
        }

    # --------------------------------

    def from_dict(self, data):
        """Restore view manager data."""

        data = data or {}
        self.views = [
            ViewState.from_dict(item)
            for item in data.get("views", [])
        ]
        self.current = self.get(data.get("current")) or (self.views[0] if self.views else None)

    # --------------------------------

    def _unique_name(self, name, current=None):

        base = str(name or "View").strip() or "View"
        names = {
            view.name for view in self.views
            if view is not current
        }

        if base not in names:
            return base

        index = 1

        while f"{base} {index}" in names:
            index += 1

        return f"{base} {index}"


class DisplayModeManager:
    """Workspace-owned display mode state for Renderer3D."""

    def __init__(self):

        self.current_mode = "wireframe"

    # --------------------------------

    def set_mode(self, mode):
        """Set the active display mode."""

        self.current_mode = _normalize_display_mode(mode)

        return self.current_mode

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe display mode data."""

        return {"current_mode": self.current_mode}

    # --------------------------------

    def from_dict(self, data):
        """Restore display mode data."""

        self.set_mode((data or {}).get("current_mode", self.current_mode))


class VisualStyle:
    """Reusable 3D visual style consumed by Renderer3D."""

    def __init__(
        self,
        name="Default",
        background="#16191d",
        grid_visible=True,
        axis_visible=True,
        lighting_enabled=False,
        edge_visible=True,
        face_visible=True,
        selection_color="#ffeb3b",
        hover_color="#80deea",
        snap_color="#ffab40",
        material_settings=None,
    ):

        self.name = str(name)
        self.background = background
        self.grid_visible = bool(grid_visible)
        self.axis_visible = bool(axis_visible)
        self.lighting_enabled = bool(lighting_enabled)
        self.edge_visible = bool(edge_visible)
        self.face_visible = bool(face_visible)
        self.selection_color = selection_color
        self.hover_color = hover_color
        self.snap_color = snap_color
        self.material_settings = dict(material_settings or {})

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe visual style data."""

        return dict(self.__dict__)

    # --------------------------------

    @staticmethod
    def from_dict(data):
        """Create a visual style from persisted data."""

        data = data or {}

        return VisualStyle(
            data.get("name", "Default"),
            data.get("background", "#16191d"),
            data.get("grid_visible", True),
            data.get("axis_visible", True),
            data.get("lighting_enabled", False),
            data.get("edge_visible", True),
            data.get("face_visible", True),
            data.get("selection_color", "#ffeb3b"),
            data.get("hover_color", "#80deea"),
            data.get("snap_color", "#ffab40"),
            data.get("material_settings", {}),
        )


class VisualStyleManager:
    """Workspace-owned visual style manager."""

    def __init__(self):

        self.styles = []
        self.current = None
        self._create_defaults()

    # --------------------------------

    def add(self, style):
        """Store a visual style."""

        if style not in self.styles:
            style.name = self._unique_name(style.name, style)
            self.styles.append(style)

        if self.current is None:
            self.current = style

        return style

    # --------------------------------

    def set_current(self, style):
        """Set the active visual style."""

        target = self.get(style)

        if target is not None:
            self.current = target

        return self.current

    # --------------------------------

    def rename(self, style, new_name):
        """Rename a visual style."""

        target = self.get(style)

        if target is None:
            return False

        target.name = self._unique_name(new_name, target)

        return True

    # --------------------------------

    def delete(self, style):
        """Delete a non-default visual style."""

        target = self.get(style)

        if target is None or target.name == "Default":
            return False

        self.styles.remove(target)

        if self.current is target:
            self.current = self.get("Default") or (self.styles[0] if self.styles else None)

        return True

    # --------------------------------

    def get(self, style):
        """Return a visual style by object or name."""

        if isinstance(style, VisualStyle):
            return style if style in self.styles else None

        for item in self.styles:
            if item.name == style:
                return item

        return None

    # --------------------------------

    def names(self):
        """Return visual style names."""

        return [style.name for style in self.styles]

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe visual style manager data."""

        return {
            "current": getattr(self.current, "name", "Default"),
            "styles": [style.to_dict() for style in self.styles],
        }

    # --------------------------------

    def from_dict(self, data):
        """Restore visual style manager data."""

        data = data or {}
        items = data.get("styles", [])

        if items:
            self.styles = [
                VisualStyle.from_dict(item)
                for item in items
            ]

        self.current = self.get(data.get("current")) or self.get("Default") or (
            self.styles[0] if self.styles else None
        )

    # --------------------------------

    def _create_defaults(self):

        self.styles = [
            VisualStyle("Default"),
            VisualStyle(
                "Dark Technical",
                background="#101418",
                grid_visible=True,
                axis_visible=True,
                edge_visible=True,
                face_visible=True,
            ),
            VisualStyle(
                "Presentation",
                background="#20242b",
                grid_visible=False,
                axis_visible=True,
                selection_color="#ffd54f",
            ),
        ]
        self.current = self.styles[0]

    # --------------------------------

    def _unique_name(self, name, current=None):

        base = str(name or "Visual Style").strip() or "Visual Style"
        names = {
            style.name for style in self.styles
            if style is not current
        }

        if base not in names:
            return base

        index = 1

        while f"{base} {index}" in names:
            index += 1

        return f"{base} {index}"


def _normalize_display_mode(mode):

    value = str(mode or "wireframe").strip().lower().replace(" ", "_").replace("-", "_")

    if value not in DISPLAY_MODES:
        return "wireframe"

    return value

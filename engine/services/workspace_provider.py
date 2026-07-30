from __future__ import annotations

from typing import Any


class WorkspaceProvider:
    """Resolves the current active workspace from an application facade."""

    def __init__(self, app: Any) -> None:
        """Store the application facade that owns the active workspace."""

        object.__setattr__(self, "_app", app)

    @property
    def app(self) -> Any:
        """Return the application facade used by this provider."""

        return object.__getattribute__(self, "_app")

    @property
    def current(self) -> Any:
        """Return the active workspace from the application facade."""

        return self.app.workspace

    def current_workspace(self) -> Any:
        """Return the active workspace from the application facade."""

        return self.current

    def __getattr__(self, name: str) -> Any:
        """Delegate unknown attribute access to the active workspace."""

        return getattr(self.current, name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Delegate mutable workspace attributes to the active workspace."""

        if name == "_app":
            object.__setattr__(self, name, value)
            return
        setattr(self.current, name, value)

    def __bool__(self) -> bool:
        """Return True when an active workspace is available."""

        return self.current is not None

    def __repr__(self) -> str:
        """Return a diagnostic representation of the active workspace."""

        workspace = self.current
        name = getattr(workspace, "name", "None")
        return f"{self.__class__.__name__}(current={name!r})"

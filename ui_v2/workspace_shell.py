from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class RibbonHost(QWidget):
    """Top shell region that hosts the injected ribbon widget."""

    def __init__(self, ribbon: QWidget, parent: QWidget | None = None):
        """Create a ribbon host from an externally supplied ribbon widget."""

        super().__init__(parent)

        self._ribbon = ribbon
        self.setObjectName("RibbonHost")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._ribbon)

    def ribbon(self) -> QWidget:
        """Return the hosted ribbon widget."""

        return self._ribbon


class PropertiesSidebar(QFrame):
    """Right shell region that hosts the injected property panel widget."""

    INITIAL_WIDTH = 300
    MINIMUM_WIDTH = 260
    MAXIMUM_WIDTH = 420

    def __init__(self, property_panel: QWidget, parent: QWidget | None = None):
        """Create a properties sidebar from an externally supplied panel."""

        super().__init__(parent)

        self._property_panel = property_panel
        self.setObjectName("PropertiesSidebar")
        self.setFrameShape(QFrame.NoFrame)
        self.setMinimumWidth(self.MINIMUM_WIDTH)
        self.setMaximumWidth(self.MAXIMUM_WIDTH)
        self.resize(self.INITIAL_WIDTH, self.height())
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._property_panel)

    def property_panel(self) -> QWidget:
        """Return the hosted property panel widget."""

        return self._property_panel


class CommandLineHost(QWidget):
    """Bottom shell region that hosts the injected command bar widget."""

    def __init__(self, command_bar: QWidget, parent: QWidget | None = None):
        """Create a command-line host from an externally supplied command bar."""

        super().__init__(parent)

        self._command_bar = command_bar
        self.setObjectName("CommandLineHost")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._command_bar)

    def command_bar(self) -> QWidget:
        """Return the hosted command bar widget."""

        return self._command_bar


class StatusBarHost(QWidget):
    """Bottom shell region that hosts the injected status bar widget."""

    def __init__(self, status_bar: QWidget, parent: QWidget | None = None):
        """Create a status-bar host from an externally supplied status bar."""

        super().__init__(parent)

        self._status_bar = status_bar
        self.setObjectName("StatusBarHost")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._status_bar)

    def status_bar(self) -> QWidget:
        """Return the hosted status bar widget."""

        return self._status_bar


class WorkspaceShell(QWidget):
    """Reusable viewport-first application shell composed from injected widgets."""

    def __init__(
        self,
        ribbon: QWidget,
        left_toolbox: QWidget,
        viewport_area: QWidget,
        property_panel: QWidget,
        command_bar: QWidget,
        status_bar: QWidget,
        parent: QWidget | None = None,
    ):
        """Create the shell without instantiating or routing child widgets."""

        super().__init__(parent)

        self._left_toolbox = left_toolbox
        self._viewport_area = viewport_area
        self._ribbon_host = RibbonHost(ribbon, self)
        self._properties_sidebar = PropertiesSidebar(property_panel, self)
        self._command_line_host = CommandLineHost(command_bar, self)
        self._status_bar_host = StatusBarHost(status_bar, self)

        self.setObjectName("WorkspaceShell")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._configure_child_sizing()
        self._build_layout()
        self._apply_style()

    def ribbon(self) -> QWidget:
        """Return the shell ribbon widget."""

        return self._ribbon_host.ribbon()

    def left_toolbox(self) -> QWidget:
        """Return the shell left toolbox widget."""

        return self._left_toolbox

    def viewport_area(self) -> QWidget:
        """Return the shell viewport area widget."""

        return self._viewport_area

    def property_panel(self) -> QWidget:
        """Return the shell property panel widget."""

        return self._properties_sidebar.property_panel()

    def command_bar(self) -> QWidget:
        """Return the shell command bar widget."""

        return self._command_line_host.command_bar()

    def status_bar(self) -> QWidget:
        """Return the shell status bar widget."""

        return self._status_bar_host.status_bar()

    def _configure_child_sizing(self) -> None:
        """Configure layout sizing so the viewport naturally dominates."""

        self._left_toolbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self._viewport_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._properties_sidebar.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Expanding,
        )

    def _build_layout(self) -> None:
        """Compose the permanent application shell layout."""

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        body = QWidget(self)
        body.setObjectName("WorkspaceShellBody")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        body_layout.addWidget(self._left_toolbox)
        body_layout.addWidget(self._viewport_area, 1)
        body_layout.addWidget(self._properties_sidebar)

        root_layout.addWidget(self._ribbon_host)
        root_layout.addWidget(body, 1)
        root_layout.addWidget(self._command_line_host)
        root_layout.addWidget(self._status_bar_host)

    def _apply_style(self) -> None:
        """Apply neutral shell styling without affecting child behavior."""

        self.setStyleSheet(
            """
            QWidget#WorkspaceShell {
                background-color: #101318;
            }

            QWidget#WorkspaceShellBody {
                background-color: #101318;
            }

            QFrame#PropertiesSidebar {
                background-color: #181c22;
                border-left: 1px solid #2a2f38;
            }
            """
        )

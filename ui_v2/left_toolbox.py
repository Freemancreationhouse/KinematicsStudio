from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class ToolboxAction:
    """Definition for a left-toolbox action button."""

    action_id: str
    label: str
    icon_text: str
    tooltip: str


class LeftToolbox(QWidget):
    """Permanent narrow action toolbox for the workspace shell."""

    actionTriggered = Signal(str)

    WIDTH = 68

    def __init__(self, parent: QWidget | None = None):
        """Create the toolbox as a backend-independent action emitter."""

        super().__init__(parent)

        self._buttons: dict[str, QPushButton] = {}
        self._active_action_id: str | None = None

        self.setObjectName("LeftToolbox")
        self.setFixedWidth(self.WIDTH)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setAttribute(Qt.WA_StyledBackground, True)

        self._build_ui()
        self._apply_style()

    def enable_action(self, action_id: str, enabled: bool) -> None:
        """Enable or disable a toolbox action by identifier."""

        button = self._buttons.get(action_id)
        if button is not None:
            button.setEnabled(enabled)

    def set_active_action(self, action_id: str) -> None:
        """Mark a toolbox action as active and update button styling."""

        if action_id not in self._buttons:
            return

        self._active_action_id = action_id
        for current_action_id, button in self._buttons.items():
            button.setProperty("active", current_action_id == action_id)
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()

    def clear_active_action(self) -> None:
        """Clear the active action highlight from every toolbox button."""

        self._active_action_id = None
        for button in self._buttons.values():
            button.setProperty("active", False)
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()

    def _build_ui(self) -> None:
        """Build the scrollable vertical button layout."""

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        scroll_area = QScrollArea(self)
        scroll_area.setObjectName("LeftToolboxScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        root_layout.addWidget(scroll_area)

        content = QWidget(scroll_area)
        content.setObjectName("LeftToolboxContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(6, 8, 6, 8)
        content_layout.setSpacing(6)

        for action in self._actions():
            button = self._create_button(action)
            content_layout.addWidget(button)
            self._buttons[action.action_id] = button

        content_layout.addStretch(1)
        scroll_area.setWidget(content)

    def _create_button(self, action: ToolboxAction) -> QPushButton:
        """Create a single action button for the toolbox."""

        button = QPushButton(f"{action.icon_text}\n{action.label}", self)
        button.setObjectName("LeftToolboxButton")
        button.setToolTip(action.tooltip)
        button.setCursor(Qt.PointingHandCursor)
        button.setCheckable(False)
        button.setProperty("actionId", action.action_id)
        button.setProperty("active", False)
        button.setMinimumHeight(54)
        button.setMaximumWidth(56)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.clicked.connect(
            lambda checked=False, action_id=action.action_id: self._emit_action(
                action_id
            )
        )
        return button

    def _emit_action(self, action_id: str) -> None:
        """Emit the selected action identifier without performing any work."""

        self.actionTriggered.emit(action_id)

    def _actions(self) -> tuple[ToolboxAction, ...]:
        """Return the fixed set of production toolbox actions."""

        return (
            ToolboxAction("select", "Select", "↖", "Select objects in the workspace."),
            ToolboxAction("draw", "Draw", "✎", "Open drawing tools."),
            ToolboxAction("modify", "Modify", "✣", "Open modification tools."),
            ToolboxAction("view_2d", "2D", "□", "Switch to the 2D workspace view."),
            ToolboxAction("view_3d", "3D", "◇", "Switch to the 3D workspace view."),
            ToolboxAction("panels", "Panels", "▤", "Open workspace panels."),
            ToolboxAction(
                "command_palette",
                "Cmd",
                "⌘",
                "Open the command palette.",
            ),
            ToolboxAction("focus_mode", "Focus", "◉", "Enter focus mode."),
        )

    def _apply_style(self) -> None:
        """Apply the dark production toolbox appearance using Qt style sheets."""

        self.setStyleSheet(
            """
            QWidget#LeftToolbox {
                background-color: #15181d;
                border-right: 1px solid #2a2f38;
            }

            QScrollArea#LeftToolboxScrollArea {
                background-color: transparent;
                border: none;
            }

            QWidget#LeftToolboxContent {
                background-color: transparent;
            }

            QPushButton#LeftToolboxButton {
                background-color: #1d222a;
                border: 1px solid #2d3440;
                border-radius: 8px;
                color: #d7dde7;
                font-size: 10px;
                font-weight: 600;
                padding: 4px 2px;
                text-align: center;
            }

            QPushButton#LeftToolboxButton:hover {
                background-color: #26303c;
                border-color: #3f8cff;
                color: #ffffff;
            }

            QPushButton#LeftToolboxButton:pressed {
                background-color: #315d9f;
                border-color: #68a7ff;
            }

            QPushButton#LeftToolboxButton[active="true"] {
                background-color: #2563eb;
                border-color: #78b7ff;
                color: #ffffff;
            }

            QPushButton#LeftToolboxButton:disabled {
                background-color: #181b21;
                border-color: #242933;
                color: #666d78;
            }

            QScrollBar:vertical {
                background: #15181d;
                width: 6px;
                margin: 0;
            }

            QScrollBar::handle:vertical {
                background: #3a4350;
                border-radius: 3px;
                min-height: 24px;
            }

            QScrollBar::handle:vertical:hover {
                background: #4b5665;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
                width: 0;
            }
            """
        )

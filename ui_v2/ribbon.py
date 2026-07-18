from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
)

from ui_v2.ribbon_project import ProjectRibbon
from ui_v2.ribbon_draw import DrawRibbon
from ui_v2.ribbon_modify import ModifyRibbon
from ui_v2.ribbon_blocks import BlocksRibbon
from ui_v2.ribbon_ai import AIRibbon
from ui_v2.ribbon_machine import MachineRibbon


class Ribbon(QWidget):

    def __init__(self, tool_manager):

        super().__init__()

        self.tool_manager = tool_manager

        layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()

        layout.addWidget(self.tabs)

        self.tabs.addTab(
            ProjectRibbon(tool_manager),
            "Project"
        )

        self.tabs.addTab(
            DrawRibbon(tool_manager),
            "Draw"
        )

        self.tabs.addTab(
            ModifyRibbon(tool_manager),
            "Modify"
        )

        self.tabs.addTab(
            BlocksRibbon(tool_manager),
            "Blocks"
        )

        self.tabs.addTab(
            AIRibbon(),
            "AI"
        )

        self.tabs.addTab(
            MachineRibbon(),
            "Machine"
        )

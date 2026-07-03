from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolBar


class MainToolbar(QToolBar):

    def __init__(self, tool_manager):

        super().__init__("Tools")

        self.tool_manager = tool_manager

        self.setMovable(False)

        self.create_actions()

    # -------------------------------------------------

    def create_actions(self):

        tools = [

            ("Select", "SelectTool"),
            ("Line", "LineTool"),
            ("Rectangle", "RectangleTool"),
            ("Circle", "CircleTool"),
            ("Move", "MoveTool"),
            ("Smart", "SmartSketchTool"),

        ]

        for text, tool_name in tools:

            action = QAction(text, self)

            action.triggered.connect(
                lambda checked=False, name=tool_name:
                self.tool_manager.activate(name)
            )

            self.addAction(action)
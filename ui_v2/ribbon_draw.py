from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QPushButton,
)


class DrawRibbon(QWidget):

    def __init__(self, tool_manager):

        super().__init__()

        self.tool_manager = tool_manager

        layout = QGridLayout(self)

        tools = [

            ("Select", "SelectTool"),
            ("Line", "LineTool"),
            ("Rectangle", "RectangleTool"),
            ("Circle", "CircleTool"),
            ("Polyline", "PolylineTool"),
            ("Closed Poly", "ClosedPolylineTool"),
            ("Spline", "SplineTool"),
            ("Text", "TextTool"),
            ("MText", "MTextTool"),
            ("Leader", "LeaderTool"),
            ("Hatch", "HatchTool"),
            ("Linear Dim", "LinearDimensionTool"),
            ("Aligned Dim", "AlignedDimensionTool"),
            ("Radius Dim", "RadiusDimensionTool"),
            ("Diameter Dim", "DiameterDimensionTool"),
            ("Angular Dim", "AngularDimensionTool"),
            ("Move", "MoveTool"),
            ("Smart", "SmartSketchTool"),

        ]

        row = 0
        col = 0

        for text, tool in tools:

            button = QPushButton(text)

            button.setMinimumHeight(42)
            button.setToolTip(f"Activate {text}.")

            button.clicked.connect(

                lambda checked=False, name=tool:

                self.tool_manager.activate(name)

            )

            layout.addWidget(

                button,

                row,

                col

            )

            col += 1

            if col == 3:

                col = 0
                row += 1

        layout.setRowStretch(row + 1, 1)

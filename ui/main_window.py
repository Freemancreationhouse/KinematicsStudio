from math import atan2, degrees, sqrt

# DEPRECATED: Legacy main window retained for backward compatibility.
# V2 uses ui_v2.main_window.MainWindow.

from ui.canvas import Canvas
from ui.layer_panel import LayerPanel
from ui.command_line import CommandLine

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QPushButton,
    QStatusBar,
    QDockWidget,
    QFormLayout,
    QLineEdit,
)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Kinematics Studio v1.0")
        self.resize(1700, 950)

        # ---------------- MENU ----------------

        menu = self.menuBar()

        menu.addMenu("File")
        menu.addMenu("Edit")
        menu.addMenu("View")
        menu.addMenu("Draw")
        menu.addMenu("Machine")
        menu.addMenu("Help")

        # ---------------- CENTRAL ----------------

        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)

        # ---------------- SIDEBAR ----------------

        sidebar = QListWidget()

        sidebar.addItems([
            "Dashboard",
            "Designer",
            "Geometry",
            "Machine",
            "Library",
            "Settings"
        ])

        sidebar.setMinimumWidth(170)
        sidebar.setMaximumWidth(170)

        layout.addWidget(sidebar)

        # ---------------- TOOLBAR ----------------

        tool_panel = QWidget()

        tool_layout = QVBoxLayout(tool_panel)

        self.canvas = Canvas()

        buttons = [

            ("Select","select"),
            ("Move","move"),
            ("Smart Sketch","smart"),
            ("Polyline","polyline"),
            ("Rectangle","rectangle"),
            ("Circle","circle"),

            ("Trim","trim"),
            ("Offset","offset"),
            ("Mirror","mirror")

        ]

        for text,tool in buttons:

            b = QPushButton(text)
            if tool == "smart":

             b.clicked.connect(

            self.canvas.tool_manager.toggle_smart_sketch

        )
        else:
           
            b.clicked.connect(

                lambda checked=False,t=tool:

                self.canvas.tool_manager.set_tool(t)

            )

            tool_layout.addWidget(b)

        tool_layout.addSpacing(20)

        snaps=[

            ("END","endpoint"),
            ("MID","midpoint"),
            ("CEN","center"),
            ("INT","intersection")

        ]

        for text,snap in snaps:

            b=QPushButton(text)

            b.clicked.connect(

                lambda checked=False,s=snap:

                self.canvas.tool_manager.toggle_snap(s)

            )

            tool_layout.addWidget(b)

        tool_layout.addStretch()

        tool_panel.setMinimumWidth(150)

        layout.addWidget(tool_panel)

        # ---------------- CANVAS ----------------

        layout.addWidget(self.canvas)

        # ==================================================
        # PROPERTIES
        # ==================================================

        self.propDock=QDockWidget("Properties",self)

        self.addDockWidget(
            Qt.RightDockWidgetArea,
            self.propDock
        )

        prop=QWidget()

        form=QFormLayout(prop)

        self.type_edit=QLineEdit()

        self.type_edit.setReadOnly(True)

        self.x1=QLineEdit()
        self.y1=QLineEdit()

        self.x2=QLineEdit()
        self.y2=QLineEdit()

        self.length=QLineEdit()

        self.angle=QLineEdit()

        for w in [

            self.x1,
            self.y1,
            self.x2,
            self.y2,
            self.length,
            self.angle

        ]:

            w.setReadOnly(True)

        form.addRow("Type",self.type_edit)
        form.addRow("X1",self.x1)
        form.addRow("Y1",self.y1)
        form.addRow("X2",self.x2)
        form.addRow("Y2",self.y2)
        form.addRow("Length",self.length)
        form.addRow("Angle",self.angle)

        self.propDock.setWidget(prop)

        # ==================================================
        # LAYER PANEL
        # ==================================================

        self.layerDock=QDockWidget("Layers",self)

        self.addDockWidget(

            Qt.LeftDockWidgetArea,

            self.layerDock

        )

        self.layerDock.setWidget(

            LayerPanel(

                self.canvas.project

            )

        )

        # ==================================================
        # CALLBACK
        # ==================================================

        self.canvas.project.on_selection_changed(

            self.update_properties

        )

        self.update_properties(None)

        # ==================================================

        self.setStatusBar(QStatusBar())

        self.statusBar().showMessage("Ready")

        # ---------------- Command Line ----------------

        self.command_line = CommandLine(
            self.canvas.tool_manager
        )

        self.command_line.setMinimumHeight(30)
        self.command_line.setMinimumWidth(500)

        self.statusBar().addPermanentWidget(
            self.command_line,
             1
        )

    # ======================================================

    def update_properties(self,entity):

        if entity is None:

            self.type_edit.setText("None")

            for w in [

                self.x1,
                self.y1,
                self.x2,
                self.y2,
                self.length,
                self.angle

            ]:

                w.clear()

            return

        # ---------- LINE ----------

        if hasattr(entity,"start"):

            self.type_edit.setText("Line")

            self.x1.setText(str(entity.start.x()))
            self.y1.setText(str(entity.start.y()))

            self.x2.setText(str(entity.end.x()))
            self.y2.setText(str(entity.end.y()))

            dx=entity.end.x()-entity.start.x()
            dy=entity.end.y()-entity.start.y()

            self.length.setText(

                f"{sqrt(dx*dx+dy*dy):.2f}"

            )

            self.angle.setText(

                f"{degrees(atan2(dy,dx)):.2f}"

            )

            return

        # ---------- RECTANGLE ----------

        if hasattr(entity,"p1"):

            self.type_edit.setText("Rectangle")

            self.x1.setText(str(entity.p1.x()))
            self.y1.setText(str(entity.p1.y()))

            self.x2.setText(str(entity.p2.x()))
            self.y2.setText(str(entity.p2.y()))

            self.length.setText(

                str(abs(entity.p2.x()-entity.p1.x()))

            )

            self.angle.setText(

                str(abs(entity.p2.y()-entity.p1.y()))

            )

            return

        # ---------- CIRCLE ----------

        if hasattr(entity, "center"):

            self.type_edit.setText("Circle")

            self.x1.setText(str(entity.center.x()))
            self.y1.setText(str(entity.center.y()))

            self.x2.clear()
            self.y2.clear()

            self.length.setText(f"{entity.radius:.2f}")

            self.angle.clear()

            return

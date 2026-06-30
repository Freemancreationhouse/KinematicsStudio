from ui.canvas import Canvas
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QListWidget,
    QLabel,
    QStatusBar,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Kinematics Studio v0.1 - Genesis")
        self.resize(1400, 900)
        menu = self.menuBar()

        file_menu = menu.addMenu("File")
        edit_menu = menu.addMenu("Edit")
        view_menu = menu.addMenu("View")
        machine_menu = menu.addMenu("Machine")
        tools_menu = menu.addMenu("Tools")
        help_menu = menu.addMenu("Help")

        # Main Widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)

        # Sidebar
        self.sidebar = QListWidget()

        self.sidebar.addItems([
            "🏠 Dashboard",
            "✏ Designer",
            "📐 Geometry",
            "🤖 AI Studio",
            "🎮 Machine",
            "📚 Library",
            "⚙ Settings"
        ])

        self.sidebar.setMinimumWidth(230)
        self.sidebar.setMaximumWidth(230)

        layout.addWidget(self.sidebar)

        # Main Canvas
        self.canvas=Canvas()

        layout.addWidget(self.canvas)

        self.canvas.setStyleSheet("""
        background:#252525;
        color:white;
        font-size:32px;
        font-weight:bold;                         
        """)

        
        layout.addWidget(self.canvas)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")
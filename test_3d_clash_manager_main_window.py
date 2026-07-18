import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from ui_v2.main_window import MainWindow


qt_app = QApplication.instance() or QApplication([])

window = MainWindow()

assert hasattr(window, "clash_panel")
assert window.clash_dock.objectName() == "ClashManagerDock"
assert window.clash_panel.workspace is window.canvas.app.workspace

window.close()

print("3d-clash-manager-main-window-ok")

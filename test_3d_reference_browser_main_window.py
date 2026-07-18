import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from ui_v2.main_window import MainWindow


qt_app = QApplication.instance() or QApplication([])

window = MainWindow()

assert hasattr(window, "reference_panel")
assert window.reference_dock.objectName() == "ReferenceBrowserDock"
assert window.reference_panel.workspace is window.canvas.app.workspace
assert window.ribbon is not None

window.close()

print("3d-reference-browser-main-window-ok")

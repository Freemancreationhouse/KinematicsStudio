import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from ui_v2.main_window import MainWindow


qt_app = QApplication.instance() or QApplication([])

window = MainWindow()

assert hasattr(window, "reference_layer_panel")
assert hasattr(window, "coordination_panel")
assert window.reference_layer_dock.objectName() == "ReferenceLayerDock"
assert window.coordination_dock.objectName() == "CoordinationDock"

window.close()

print("3d-reference-q-main-window-ok")

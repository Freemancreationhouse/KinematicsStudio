import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from ui_v2.main_window import MainWindow


qt_app = QApplication.instance() or QApplication([])

window = MainWindow()

assert hasattr(window, "clash_dashboard_panel")
assert window.clash_dashboard_dock.objectName() == "ClashDashboardDock"
assert window.clash_dashboard_panel.workspace is window.canvas.app.workspace

window.close()

print("3d-clash-dashboard-main-window-ok")

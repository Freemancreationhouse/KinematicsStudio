import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QPushButton

from ui_v2.main_window import MainWindow
from ui_v2.property_panel import PropertyPanel
from ui_v2.ribbon_draw import DrawRibbon
from ui_v2.status_bar import StudioStatusBar


qt_app = QApplication.instance() or QApplication([])
settings = QSettings("Kinematics Studio", "Kinematics Studio V2")
settings.remove("main_window")

window = MainWindow()
docks = [
    window.explorer_dock,
    window.property_dock,
    window.layer_dock,
    window.dimension_dock,
    window.pattern_dock,
    window.block_dock,
    window.group_dock,
    window.selection_set_dock,
    window.constraint_dock,
    window.project_dock,
]

assert all(dock.objectName() for dock in docks)
assert all(dock.toolTip() for dock in docks)

window.close()
assert settings.value("main_window/geometry") is not None
assert settings.value("main_window/state") is not None
settings.remove("main_window")

status_bar = StudioStatusBar()
assert status_bar.coords.toolTip()
assert status_bar.snap.toolTip()
assert status_bar.undo.text() == "Undo: No"

property_panel = PropertyPanel()
assert property_panel.x.placeholderText()
assert property_panel.layer.toolTip()

ribbon = DrawRibbon(window.canvas.app.tool_manager)
assert any(
    button.toolTip()
    for button in ribbon.findChildren(QPushButton)
)

print("production-ux-polish-ok")

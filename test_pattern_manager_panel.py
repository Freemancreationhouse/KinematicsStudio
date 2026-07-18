import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication

from engine.workspace import Workspace
from ui_v2.pattern_manager_panel import PatternManagerPanel


app = QApplication.instance() or QApplication([])

workspace = Workspace("Pattern Manager")
panel = PatternManagerPanel(workspace)

assert workspace.current_pattern.name == "SOLID"
assert panel.table.rowCount() == 3
assert workspace.pattern_manager.get("ANSI31") is not None

custom = workspace.pattern_manager.create("Custom", scale=12, angle=30)
workspace.set_current_pattern(custom)
panel.refresh()

assert panel.table.rowCount() == 4
assert panel.table.item(3, 0).text() == "✓"
assert panel.table.item(3, 1).text() == "Custom"
assert panel.table.item(3, 3).text() == "12.00"
assert panel.table.item(3, 4).text() == "30.00"

print("pattern-manager-ok")

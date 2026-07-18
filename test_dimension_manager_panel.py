import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication

from engine.workspace import Workspace
from ui_v2.dimension_manager_panel import DimensionManagerPanel


app = QApplication.instance() or QApplication([])

workspace = Workspace("Dimension Manager")
panel = DimensionManagerPanel(workspace)

assert workspace.current_dimension_style.name == "Standard"
assert panel.table.rowCount() == 1

custom = workspace.create_dimension_style(
    "Custom",
    text_height=14,
    arrow_size=7,
    precision=3,
    units="mm",
)
panel.refresh()

assert panel.table.rowCount() == 2
assert panel.table.item(1, 1).text() == "Custom"
assert panel.table.item(1, 2).text() == "14.00"
assert panel.table.item(1, 3).text() == "7.00"
assert panel.table.item(1, 4).text() == "3"
assert panel.table.item(1, 5).text() == "mm"

workspace.set_current_dimension_style(custom)
panel.refresh()
assert panel.table.item(1, 0).text() == "✓"

assert workspace.rename_dimension_style(custom, "Renamed")
assert workspace.dimension_style_manager.get("Renamed") is custom
assert workspace.delete_dimension_style(custom)
assert workspace.dimension_style_manager.get("Renamed") is None
assert workspace.current_dimension_style.name == "Standard"

print("dimension-manager-ok")

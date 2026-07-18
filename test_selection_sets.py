import os
import tempfile

from PySide6.QtWidgets import QApplication

from engine.entities import LineEntity, RectangleEntity
from engine.geometry import Vector2
from engine.storage.project import ProjectSerializer
from engine.workspace import Workspace
from ui_v2.selection_set_manager_panel import SelectionSetManagerPanel


workspace = Workspace("Selection Sets")
line = LineEntity(Vector2(0, 0), Vector2(10, 0))
rectangle = RectangleEntity(Vector2(20, 20), Vector2(40, 40))

workspace.add_entity(line)
workspace.add_entity(rectangle)

selection = workspace.selection
selection.select_many([line, rectangle])
created = selection.create_set("Primary")
assert created.count == 2
assert selection.set_names() == ["Primary"]

selection.select(line)
selection.update_set("Primary")
assert selection.selection_sets["Primary"].entities == [line]

assert selection.rename_set("Primary", "Renamed")
assert selection.set_names() == ["Renamed"]

selection.clear()
assert selection.recall_set("Renamed", workspace) == [line]

app = QApplication.instance() or QApplication([])
panel = SelectionSetManagerPanel(workspace)
panel.refresh()
assert panel.table.rowCount() == 1

serializer = ProjectSerializer()
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "selection_sets.ksproj")
    serializer.save(workspace, path)
    restored = serializer.load(path)

assert restored.selection.set_names() == ["Renamed"]
restored.selection.recall_set("Renamed", restored)
assert len(restored.selection.selected) == 1

assert selection.delete_set("Renamed")
assert selection.set_names() == []

print("selection-sets-ok")

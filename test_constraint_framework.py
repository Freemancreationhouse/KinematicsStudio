import tempfile
from pathlib import Path

from PySide6.QtWidgets import QApplication

from engine.commands import (
    CreateConstraintCommand,
    DeleteConstraintCommand,
    EnableConstraintCommand,
    RemoveEntityCommand,
    RenameConstraintCommand,
    UpdateConstraintCommand,
)
from engine.entities import CircleEntity, LineEntity
from engine.export import ExportManager
from engine.geometry import Vector2
from engine.storage.project import ProjectSerializer
from engine.workspace import Workspace
from ui_v2.constraint_manager_panel import ConstraintManagerPanel
from ui_v2.property_panel import PropertyPanel


workspace = Workspace("Constraint Framework")
line = LineEntity(Vector2(0, 0), Vector2(100, 10))
line_b = LineEntity(Vector2(0, 20), Vector2(100, 20))
vertical = LineEntity(Vector2(20, 0), Vector2(20, 80))
circle = CircleEntity(Vector2(200, 40), 25)
circle_b = CircleEntity(Vector2(200, 40), 10)

for entity in (line, line_b, vertical, circle, circle_b):
    workspace.add_entity(entity)

geometric = [
    ("Horizontal", [line]),
    ("Vertical", [vertical]),
    ("Parallel", [line, line_b]),
    ("Perpendicular", [line_b, vertical]),
    ("Coincident", [line, line_b]),
    ("Tangent", [line_b, circle]),
    ("Equal", [line, line_b]),
    ("Concentric", [circle, circle_b]),
    ("Symmetry", [line, line_b]),
    ("Midpoint", [line]),
]
dimensional = [
    ("Distance", [line], 120.0),
    ("Horizontal Distance", [line], 120.0),
    ("Vertical Distance", [vertical], 80.0),
    ("Radius", [circle], 30.0),
    ("Diameter", [circle_b], 40.0),
    ("Angle", [line, line_b], 0.0),
]

for item in geometric:
    workspace.command_manager.execute(CreateConstraintCommand(workspace, item[0], item[1]))

for item in dimensional:
    workspace.command_manager.execute(CreateConstraintCommand(workspace, item[0], item[1], item[2]))

assert len(workspace.constraint_manager.constraints) == len(geometric) + len(dimensional)
assert workspace.command_manager.undo_available
assert workspace.constraint_manager.validate() in ("OK", "Under-constrained", "Over-constrained")

horizontal = workspace.constraint_manager.constraints[0]
workspace.selection.select(horizontal)
assert horizontal in workspace.selection.selected
assert horizontal in workspace.selectable_entities()

workspace.constraint_manager.solve(workspace.command_manager)
assert round(line.end.y, 6) == round(line.start.y, 6)
assert round(circle.radius, 6) == 30.0
assert round(circle_b.radius, 6) == 20.0
assert workspace.command_manager.undo_available
workspace.command_manager.undo()
workspace.command_manager.redo()

workspace.command_manager.execute(
    RenameConstraintCommand(workspace, horizontal, "Line Horizontal")
)
assert horizontal.name == "Line Horizontal"
workspace.command_manager.undo()
workspace.command_manager.redo()

workspace.command_manager.execute(EnableConstraintCommand(workspace, horizontal, False))
assert horizontal.suppressed
workspace.command_manager.undo()
assert horizontal.enabled

before = {"value": horizontal.value, "driven": horizontal.driven}
after = {"value": 15.0, "driven": True}
workspace.command_manager.execute(UpdateConstraintCommand(workspace, horizontal, before, after))
assert horizontal.value == 15.0
assert horizontal.driven
workspace.command_manager.undo()

workspace.command_manager.execute(DeleteConstraintCommand(workspace, horizontal))
assert horizontal not in workspace.constraint_manager.constraints
workspace.command_manager.undo()
assert horizontal in workspace.constraint_manager.constraints

workspace.command_manager.execute(RemoveEntityCommand(workspace.entities, line_b))
assert line_b not in workspace.entities
assert not workspace.constraint_manager.constraints_for_entity(line_b)
workspace.command_manager.undo()
assert line_b in workspace.entities
assert workspace.constraint_manager.constraints_for_entity(line_b)
workspace.command_manager.redo()
assert line_b not in workspace.entities
workspace.command_manager.undo()

workspace.command_manager.execute(CreateConstraintCommand(workspace, "Distance", [line], 10.0))
workspace.command_manager.execute(CreateConstraintCommand(workspace, "Distance", [line], 20.0))
graph = workspace.constraint_manager.solver.validate(workspace.constraint_manager)
assert graph.conflicts
assert graph.status == "Over-constrained"

app = QApplication.instance() or QApplication([])
panel = ConstraintManagerPanel(workspace)
panel.refresh()
assert panel.table.rowCount() == len(workspace.constraint_manager.constraints)

property_panel = PropertyPanel()
property_panel.set_workspace(workspace)
property_panel.show_selection([horizontal])
assert property_panel.type.text() == "Horizontal Constraint"
assert property_panel.content.text() == horizontal.name

with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / "constraints.ksproj"
    serializer = ProjectSerializer()
    serializer.save(workspace, path)
    restored = serializer.load(path)

assert len(restored.constraint_manager.constraints) == len(workspace.constraint_manager.constraints)
assert restored.constraint_manager.constraints[0].entities

context = ExportManager().context(workspace)
assert all(not getattr(item.entity, "is_constraint", False) for item in context.entities)

print("constraint-framework-ok")

from engine.commands import (
    AddSectionPlaneCommand,
    RemoveSectionPlaneCommand,
    SetActiveSectionCommand,
    UpdateSectionPlaneCommand,
)
from engine.geometry import Vector3
from engine.sections import SectionPlane
from engine.workspace import Workspace


workspace = Workspace("3D Section Command Workspace")
first = SectionPlane("First")
second = SectionPlane("Second", Vector3(10.0, 0.0, 0.0))

workspace.command_manager.execute(AddSectionPlaneCommand(workspace, first))
assert first in workspace.section_manager.sections
assert workspace.selection.first is first

workspace.command_manager.undo()
assert first not in workspace.section_manager.sections

workspace.command_manager.redo()
assert first in workspace.section_manager.sections

workspace.command_manager.execute(AddSectionPlaneCommand(workspace, second))
workspace.command_manager.execute(SetActiveSectionCommand(workspace, first, second))
assert workspace.section_manager.active is second
workspace.command_manager.undo()
assert workspace.section_manager.active is first

workspace.command_manager.execute(
    UpdateSectionPlaneCommand(
        first,
        {"enabled": first.enabled, "size": first.size},
        {"enabled": False, "size": 123.0},
    )
)
assert first.enabled is False
assert first.size == 123.0
workspace.command_manager.undo()
assert first.enabled is True
assert first.size != 123.0

workspace.command_manager.execute(RemoveSectionPlaneCommand(workspace, first))
assert first not in workspace.section_manager.sections
workspace.command_manager.undo()
assert first in workspace.section_manager.sections

print("3d-section-command-ok")

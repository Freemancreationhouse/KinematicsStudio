from engine.bim import Assembly, AssemblyMember, BIMInstance, BIMMaterial, MaterialAssignment
from engine.commands import (
    AddBIMAssemblyCommand,
    AddBIMMaterialCommand,
    AddBIMObjectCommand,
    AssignBIMMaterialCommand,
    CreateBIMProjectCommand,
    RunBIMQuantityTakeoffCommand,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.command_manager.execute(CreateBIMProjectCommand(workspace, "Command Material BIM"))
material = BIMMaterial("Command Material")
workspace.command_manager.execute(AddBIMMaterialCommand(workspace, material))
instance = BIMInstance("Command Quantity Instance")
workspace.command_manager.execute(AddBIMObjectCommand(workspace, instance))
assignment = MaterialAssignment(instance.id, material.id, 2.5, "m2")
workspace.command_manager.execute(AssignBIMMaterialCommand(workspace, assignment))
assembly = Assembly("Command Assembly")
assembly.add_member(AssemblyMember(instance.id, "Member"))
workspace.command_manager.execute(AddBIMAssemblyCommand(workspace, assembly))
workspace.command_manager.execute(RunBIMQuantityTakeoffCommand(workspace))

project = workspace.bim_manager.active_project
assert material in project.materials
assert assignment in project.material_assignments
assert assembly in project.assemblies
assert project.quantity_items
assert project.quantity_summary.by_material[material.id] == 2.5

workspace.command_manager.undo()
assert not project.quantity_items
workspace.command_manager.redo()
assert project.quantity_items
workspace.command_manager.undo()
workspace.command_manager.undo()
assert assembly not in project.assemblies
workspace.command_manager.undo()
assert assignment not in project.material_assignments
assert instance.material_assignment_id == ""

print("3d-bim-material-assembly-quantity-commands-ok")

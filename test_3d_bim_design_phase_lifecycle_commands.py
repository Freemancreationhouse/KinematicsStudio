from engine.bim import (
    BIMInstance,
    DesignOptionSet,
    LifecycleEvent,
    LifecycleState,
    OptionMembership,
    PhaseAssignment,
    PrimaryOption,
    ProjectPhase,
)
from engine.commands import (
    AddBIMDesignOptionCommand,
    AddBIMLifecycleCommand,
    AddBIMObjectCommand,
    AddBIMPhaseCommand,
    CreateBIMProjectCommand,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.command_manager.execute(CreateBIMProjectCommand(workspace, "Command Batch H BIM"))
wall = BIMInstance("Command Lifecycle Wall")
workspace.command_manager.execute(AddBIMObjectCommand(workspace, wall))

option_set = DesignOptionSet("Command Options")
option = PrimaryOption("Command Primary", option_set.id)
membership = OptionMembership(wall.id, option.id, option_set.id)
phase = ProjectPhase("Command New", "New Construction", 1)
assignment = PhaseAssignment(wall.id, phase.id)
state = LifecycleState("Designed", "Designed")
event = LifecycleEvent(wall.id, state.id, "Designed")

workspace.command_manager.execute(AddBIMDesignOptionCommand(workspace, option_set))
workspace.command_manager.execute(AddBIMDesignOptionCommand(workspace, option))
workspace.command_manager.execute(AddBIMDesignOptionCommand(workspace, membership))
workspace.command_manager.execute(AddBIMPhaseCommand(workspace, phase))
workspace.command_manager.execute(AddBIMPhaseCommand(workspace, assignment))
workspace.command_manager.execute(AddBIMLifecycleCommand(workspace, state))
workspace.command_manager.execute(AddBIMLifecycleCommand(workspace, event))

assert workspace.bim_manager.design_options_for(wall) == [membership]
assert workspace.bim_manager.phase_assignment_for(wall) == assignment
assert workspace.bim_manager.lifecycle_state_for(wall) is state

workspace.command_manager.undo()
assert workspace.bim_manager.lifecycle_state_for(wall) is None
workspace.command_manager.redo()
assert workspace.bim_manager.lifecycle_state_for(wall) is state

workspace.command_manager.undo()
workspace.command_manager.undo()
assert workspace.bim_manager.lifecycle_state_for(wall) is None
workspace.command_manager.redo()
assert state in workspace.bim_manager.active_project.lifecycle_states

print("3d-bim-design-phase-lifecycle-commands-ok")

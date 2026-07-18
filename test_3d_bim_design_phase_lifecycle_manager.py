from engine.bim import (
    BIMInstance,
    DesignOptionSet,
    LifecycleEvent,
    LifecycleState,
    OptionMembership,
    PhaseAssignment,
    PhaseFilter,
    PhaseSequence,
    PrimaryOption,
    ProjectPhase,
    SecondaryOption,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.bim_manager.create_project("Design Phase Lifecycle BIM")
wall = workspace.bim_manager.add_instance(BIMInstance("Option Wall"))
door = workspace.bim_manager.add_instance(BIMInstance("Option Door"))

option_set = workspace.bim_manager.add_design_option_item(DesignOptionSet("Facade Options"))
primary = workspace.bim_manager.add_design_option_item(PrimaryOption("Brick Facade", option_set.id))
secondary = workspace.bim_manager.add_design_option_item(SecondaryOption("Glass Facade", option_set.id))
workspace.bim_manager.design_option_manager.activate(secondary)
membership = workspace.bim_manager.add_design_option_item(OptionMembership(wall.id, secondary.id, option_set.id))

existing = workspace.bim_manager.add_phase_item(ProjectPhase("Existing", "Existing", 0))
new_phase = workspace.bim_manager.add_phase_item(ProjectPhase("New Construction", "New Construction", 1))
sequence = workspace.bim_manager.add_phase_item(PhaseSequence("Base Sequence", [existing.id, new_phase.id]))
phase_filter = workspace.bim_manager.add_phase_item(PhaseFilter("Show New", [new_phase.id]))
assignment = workspace.bim_manager.add_phase_item(PhaseAssignment(wall.id, new_phase.id))

planned = workspace.bim_manager.add_lifecycle_item(LifecycleState("Planned", "Planned"))
operational = workspace.bim_manager.add_lifecycle_item(LifecycleState("Operational", "Operational"))
event_a = workspace.bim_manager.add_lifecycle_item(LifecycleEvent(wall.id, planned.id, "Planned"))
event_b = workspace.bim_manager.add_lifecycle_item(LifecycleEvent(wall.id, operational.id, "Operational"))

option_stats = workspace.bim_manager.design_option_manager.statistics()
phase_stats = workspace.bim_manager.phase_manager.statistics()
lifecycle_stats = workspace.bim_manager.lifecycle_manager.statistics()

assert primary.primary is True
assert secondary.active is True
assert option_set.active_option_id == secondary.id
assert workspace.bim_manager.design_options_for(wall) == [membership]
assert workspace.bim_manager.design_options_for(door) == []
assert sequence.phase_ids == [existing.id, new_phase.id]
assert workspace.bim_manager.phase_assignment_for(wall) == assignment
assert workspace.bim_manager.phase_manager.visible_in_filter(wall, phase_filter) is True
assert workspace.bim_manager.lifecycle_events_for(wall) == [event_a, event_b]
assert workspace.bim_manager.lifecycle_state_for(wall) is operational
assert option_stats.option_sets == 1
assert option_stats.options == 2
assert phase_stats.assignments == 1
assert lifecycle_stats.assigned_elements == 1

print("3d-bim-design-phase-lifecycle-manager-ok")

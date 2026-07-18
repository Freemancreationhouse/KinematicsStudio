import os
import tempfile

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
from engine.cad.application import CADApplication


app = CADApplication()
workspace = app.workspace
workspace.bim_manager.create_project("Persisted Batch H BIM")
wall = workspace.bim_manager.add_instance(BIMInstance("Persisted Lifecycle Wall"))
option_set = workspace.bim_manager.add_design_option_item(DesignOptionSet("Persisted Options"))
option = workspace.bim_manager.add_design_option_item(PrimaryOption("Persisted Primary", option_set.id))
workspace.bim_manager.add_design_option_item(OptionMembership(wall.id, option.id, option_set.id))
phase = workspace.bim_manager.add_phase_item(ProjectPhase("Persisted New", "New Construction", 1))
workspace.bim_manager.add_phase_item(PhaseAssignment(wall.id, phase.id))
state = workspace.bim_manager.add_lifecycle_item(LifecycleState("Commissioned", "Commissioned"))
workspace.bim_manager.add_lifecycle_item(LifecycleEvent(wall.id, state.id, "Commissioned"))
workspace.selection.select(wall)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "bim_batch_h.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    project = restored_workspace.bim_manager.active_project
    restored_wall = project.instances[0]

    assert project.design_option_sets[0].name == "Persisted Options"
    assert project.design_options[0].name == "Persisted Primary"
    assert restored_workspace.bim_manager.design_options_for(restored_wall)[0].option_id == project.design_options[0].id
    assert restored_workspace.bim_manager.phase_assignment_for(restored_wall).created_phase_id == project.phases[0].id
    assert restored_workspace.bim_manager.lifecycle_state_for(restored_wall).name == "Commissioned"
    assert restored_wall.selected is True

print("3d-bim-design-phase-lifecycle-persistence-ok")

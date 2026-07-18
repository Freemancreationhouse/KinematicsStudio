import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

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
from engine.geometry import Vector3
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
workspace.bim_manager.create_project("Rendered Batch H BIM")
wall = BIMInstance("Rendered Lifecycle Wall", location=Vector3(0.0, 0.0, 0.0))
workspace.bim_manager.add_instance(wall)
option_set = workspace.bim_manager.add_design_option_item(DesignOptionSet("Rendered Options"))
option = workspace.bim_manager.add_design_option_item(PrimaryOption("Rendered Primary", option_set.id))
workspace.bim_manager.add_design_option_item(OptionMembership(wall.id, option.id, option_set.id))
phase = workspace.bim_manager.add_phase_item(ProjectPhase("Rendered New", "New Construction", 1))
workspace.bim_manager.add_phase_item(PhaseAssignment(wall.id, phase.id))
state = workspace.bim_manager.add_lifecycle_item(LifecycleState("Operational", "Operational"))
workspace.bim_manager.add_lifecycle_item(LifecycleEvent(wall.id, state.id, "Operational"))
workspace.selection.select(wall)

renderer = Renderer3D()
renderer.camera = Camera3D()
renderer.camera.resize(640, 480)

image = QImage(640, 480, QImage.Format_ARGB32)
image.fill(0)
painter = QPainter(image)
renderer.render(painter, workspace, 640, 480)
painter.end()

panel = PropertyPanel()
panel.set_workspace(workspace)
panel.show_selection([wall])

assert panel.type.text() == "BIMInstance"
assert panel.content.text() == "Rendered Lifecycle Wall"
assert "Options: 1" in panel.line_type.text()
assert "Phase:" in panel.line_type.text()
assert "Lifecycle: Operational" in panel.line_weight.text()
assert "Events: 1" in panel.line_weight.text()

print("3d-bim-design-phase-lifecycle-renderer-property-ok")

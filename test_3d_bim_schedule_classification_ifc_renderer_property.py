import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.bim import (
    BIMElementDefinition,
    BIMInstance,
    ClassificationCode,
    ClassificationMapping,
    ClassificationSystem,
    IFCElement,
    ScheduleDefinition,
    ScheduleField,
)
from engine.geometry import Vector3
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
workspace.bim_manager.create_project("Rendered Batch F BIM")
definition = workspace.bim_manager.add_element_definition(BIMElementDefinition("Door", "Door"))
door = BIMInstance("Rendered Door", location=Vector3(10.0, 0.0, 0.0))
door.element_definition_id = definition.id
workspace.bim_manager.add_instance(door)

schedule = ScheduleDefinition("Rendered Door Schedule", "Door")
schedule.add_field(ScheduleField("Name", "name"))
workspace.bim_manager.add_schedule(schedule)
workspace.bim_manager.build_schedule(schedule)

system = workspace.bim_manager.add_classification_system(ClassificationSystem("IFC Classification"))
code = system.add_code(ClassificationCode("IfcDoor", "Door"))
workspace.bim_manager.add_classification_mapping(ClassificationMapping(door.id, system.id, code.code, code.id))
workspace.bim_manager.add_ifc_item(IFCElement("Rendered IFC Door", door.id, door.mesh_entity_id, "IfcDoor"))
workspace.selection.select(door)

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
panel.show_selection([door])

assert panel.type.text() == "BIMInstance"
assert panel.content.text() == "Rendered Door"
assert "Classifications: 1" in panel.alignment.text()
assert "Schedules: 1 | IFC: Linked" in panel.dimension_style.text()

print("3d-bim-schedule-classification-ifc-renderer-property-ok")

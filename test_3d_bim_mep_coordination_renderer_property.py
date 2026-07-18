import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.bim import BIMInstance, ClearanceRequirement, Connector, ConnectorType, CoordinationRule, MEPComponent, MEPNetwork, MEPSystem, MEPSystemType, NetworkMembership, ServiceZone
from engine.geometry import Vector3
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
workspace.bim_manager.create_project("Rendered Batch J BIM")
equipment = BIMInstance("Rendered MEP Equipment", location=Vector3(0.0, 0.0, 0.0))
workspace.bim_manager.add_instance(equipment)
system_type = workspace.bim_manager.add_mep_item(MEPSystemType("Communication", "Communication"))
system = workspace.bim_manager.add_mep_item(MEPSystem("Data System", system_type.id))
component = workspace.bim_manager.add_mep_item(MEPComponent("Rack Component", equipment.id, system.id, "Device"))
network = workspace.bim_manager.add_mep_item(MEPNetwork("Data Network", system.id))
workspace.bim_manager.add_connector_item(NetworkMembership(network.id, component.id, "Component"))
connector_type = workspace.bim_manager.add_connector_item(ConnectorType("Cable Tray", "Communication"))
workspace.bim_manager.add_connector_item(Connector(component.id, component.id, connector_type.id))
workspace.bim_manager.add_mep_item(CoordinationRule("Data Coordination", [system.id], "Coordination"))
workspace.bim_manager.add_mep_item(ClearanceRequirement("Data Clearance", system.id, 3.0))
workspace.bim_manager.add_mep_item(ServiceZone("Data Service Zone", [system.id]))
workspace.selection.select(equipment)

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
panel.show_selection([equipment])

assert panel.type.text() == "BIMInstance"
assert panel.content.text() == "Rendered MEP Equipment"
assert "MEP Systems: 1" in panel.line_type.text()
assert "Networks: 1" in panel.line_type.text()
assert "Connectors: 1" in panel.line_type.text()
assert "MEP Rules: 1" in panel.line_weight.text()
assert "Clearances: 1" in panel.line_weight.text()

print("3d-bim-mep-coordination-renderer-property-ok")

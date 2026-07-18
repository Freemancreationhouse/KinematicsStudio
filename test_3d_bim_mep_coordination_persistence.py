import os
import tempfile

from engine.bim import BIMInstance, ClearanceRequirement, Connector, ConnectorType, CoordinationRule, MEPComponent, MEPNetwork, MEPSystem, MEPSystemType, NetworkMembership, ServiceZone
from engine.cad.application import CADApplication


app = CADApplication()
workspace = app.workspace
workspace.bim_manager.create_project("Persisted Batch J BIM")
equipment = workspace.bim_manager.add_instance(BIMInstance("Persisted Pump"))
system_type = workspace.bim_manager.add_mep_item(MEPSystemType("Plumbing", "Plumbing"))
system = workspace.bim_manager.add_mep_item(MEPSystem("Plumbing System", system_type.id))
component = workspace.bim_manager.add_mep_item(MEPComponent("Pump Component", equipment.id, system.id, "Equipment"))
network = workspace.bim_manager.add_mep_item(MEPNetwork("Pipe Network", system.id))
workspace.bim_manager.add_connector_item(NetworkMembership(network.id, component.id, "Component"))
connector_type = workspace.bim_manager.add_connector_item(ConnectorType("Pipe", "Plumbing"))
workspace.bim_manager.add_connector_item(Connector(component.id, component.id, connector_type.id))
workspace.bim_manager.add_mep_item(CoordinationRule("Pipe Rule", [system.id], "Clearance"))
workspace.bim_manager.add_mep_item(ClearanceRequirement("Pipe Clearance", system.id, 6.0))
workspace.bim_manager.add_mep_item(ServiceZone("Plumbing Zone", [system.id]))
workspace.selection.select(equipment)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "bim_batch_j.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    project = restored_workspace.bim_manager.active_project
    restored_equipment = project.instances[0]

    assert project.mep_system_types[0].name == "Plumbing"
    assert project.mep_systems[0].name == "Plumbing System"
    assert project.mep_networks[0].component_ids == [project.mep_components[0].id]
    assert project.connector_types[0].name == "Pipe"
    assert project.connectors[0].connector_type_id == project.connector_types[0].id
    assert restored_workspace.bim_manager.mep_systems_for(restored_equipment) == [project.mep_systems[0]]
    assert restored_workspace.bim_manager.mep_coordination_for(restored_equipment)["clearances"][0].clearance == 6.0
    assert restored_equipment.selected is True

print("3d-bim-mep-coordination-persistence-ok")

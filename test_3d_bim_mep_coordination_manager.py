from engine.bim import (
    BIMInstance,
    ClearanceRequirement,
    Connector,
    ConnectorType,
    CoordinationRule,
    MEPComponent,
    MEPConnector,
    MEPNetwork,
    MEPPort,
    MEPSystem,
    MEPSystemType,
    NetworkMembership,
    ServiceZone,
    SystemMembership,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.bim_manager.create_project("MEP Coordination BIM")
equipment = workspace.bim_manager.add_instance(BIMInstance("Air Handler"))
device = workspace.bim_manager.add_instance(BIMInstance("Supply Diffuser"))

workspace.bim_manager.mep_manager.ensure_default_types()
mechanical_type = workspace.bim_manager.add_mep_item(MEPSystemType("Supply Air", "Mechanical"))
system = workspace.bim_manager.add_mep_item(MEPSystem("Supply Air System", mechanical_type.id))
component_a = workspace.bim_manager.add_mep_item(MEPComponent("AHU Component", equipment.id, system.id, "Equipment"))
component_b = workspace.bim_manager.add_mep_item(MEPComponent("Diffuser Component", device.id, system.id, "Device"))
network = workspace.bim_manager.add_mep_item(MEPNetwork("Supply Air Network", system.id))
mep_connector = workspace.bim_manager.add_mep_item(MEPConnector(component_a.id, "Duct"))
port = workspace.bim_manager.add_mep_item(MEPPort(mep_connector.id, "Outlet"))
connector_type = workspace.bim_manager.add_connector_item(ConnectorType("Duct", "Mechanical"))
connector = workspace.bim_manager.add_connector_item(Connector(component_a.id, component_b.id, connector_type.id))
workspace.bim_manager.add_connector_item(NetworkMembership(network.id, component_a.id, "Component"))
workspace.bim_manager.add_connector_item(SystemMembership(system.id, network.id, "Network"))
rule = workspace.bim_manager.add_mep_item(CoordinationRule("Supply Air Coordination", [system.id], "Coordination"))
clearance = workspace.bim_manager.add_mep_item(ClearanceRequirement("Supply Clearance", system.id, 12.0))
service_zone = workspace.bim_manager.add_mep_item(ServiceZone("Mechanical Zone", [system.id]))

stats = workspace.bim_manager.mep_manager.statistics()
coordination = workspace.bim_manager.mep_coordination_for(equipment)

assert mechanical_type.name == "Supply Air"
assert component_a.id in system.component_ids
assert component_a.id in network.component_ids
assert network.id in system.network_ids
assert mep_connector.id in component_a.connector_ids
assert port.id in mep_connector.port_ids
assert connector in workspace.bim_manager.connector_manager.connectors_for(component_a)
assert workspace.bim_manager.mep_systems_for(equipment) == [system]
assert workspace.bim_manager.mep_networks_for(equipment) == [network]
assert workspace.bim_manager.connectors_for(equipment) == [mep_connector]
assert coordination["rules"] == [rule]
assert coordination["clearances"] == [clearance]
assert coordination["service_zones"] == [service_zone]
assert stats.systems == 1
assert stats.networks == 1
assert stats.components == 2
assert stats.connectors == 2

print("3d-bim-mep-coordination-manager-ok")

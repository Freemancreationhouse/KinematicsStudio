from engine.bim import BIMInstance, Connector, ConnectorType, MEPComponent, MEPNetwork, MEPSystem, MEPSystemType
from engine.commands import AddBIMConnectorCommand, AddBIMMEPCommand, AddBIMObjectCommand, CreateBIMProjectCommand
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.command_manager.execute(CreateBIMProjectCommand(workspace, "Command Batch J BIM"))
equipment = BIMInstance("Command MEP Equipment")
device = BIMInstance("Command MEP Device")
workspace.command_manager.execute(AddBIMObjectCommand(workspace, equipment))
workspace.command_manager.execute(AddBIMObjectCommand(workspace, device))

system_type = MEPSystemType("Electrical", "Electrical")
system = MEPSystem("Power System", system_type.id)
component_a = MEPComponent("Panel Component", equipment.id, system.id, "Equipment")
component_b = MEPComponent("Device Component", device.id, system.id, "Device")
network = MEPNetwork("Power Network", system.id)
connector_type = ConnectorType("Conduit", "Electrical")
connector = Connector(component_a.id, component_b.id, connector_type.id)

workspace.command_manager.execute(AddBIMMEPCommand(workspace, system_type))
workspace.command_manager.execute(AddBIMMEPCommand(workspace, system))
workspace.command_manager.execute(AddBIMMEPCommand(workspace, component_a))
workspace.command_manager.execute(AddBIMMEPCommand(workspace, component_b))
workspace.command_manager.execute(AddBIMMEPCommand(workspace, network))
workspace.command_manager.execute(AddBIMConnectorCommand(workspace, connector_type))
workspace.command_manager.execute(AddBIMConnectorCommand(workspace, connector))

assert workspace.bim_manager.mep_systems_for(equipment) == [system]
assert connector in workspace.bim_manager.connector_manager.connectors_for(component_a)

workspace.command_manager.undo()
assert workspace.bim_manager.active_project.connectors == []
workspace.command_manager.redo()
assert workspace.bim_manager.active_project.connectors == [connector]

workspace.command_manager.undo()
workspace.command_manager.undo()
assert workspace.bim_manager.active_project.connector_types == []
workspace.command_manager.redo()
assert workspace.bim_manager.active_project.connector_types == [connector_type]

print("3d-bim-mep-coordination-commands-ok")

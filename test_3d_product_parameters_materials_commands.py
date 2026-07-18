from engine.commands import (
    AddProductMaterialCommand,
    AddProductMechanicalMetadataCommand,
    AddProductParameterCommand,
    AddProductPartCommand,
    AssignProductMaterialCommand,
    CreateProductDocumentCommand,
)
from engine.product import (
    EngineeringMaterial,
    MassProperties,
    MechanicalMetadata,
    MechanicalProperties,
    ParameterSet,
    PartParameter,
    ProductPart,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.command_manager.execute(CreateProductDocumentCommand(workspace, "Command Batch B Product"))
part = ProductPart("Command Parameter Part", "mesh-command")
workspace.command_manager.execute(AddProductPartCommand(workspace, part))

parameter = PartParameter("Thickness", 3.0, "mm", "", "Sheet thickness", False, part.id)
parameter_set = ParameterSet("Manufacturing Parameters", part.id, [parameter.id])
material = EngineeringMaterial("6061 Aluminium", density=2700.0, color="#b0bec5")
metadata = MechanicalMetadata(part.id, MechanicalProperties(material.id, 2700.0, 0.001), MassProperties(2.7, 0.001, 2700.0))

workspace.command_manager.execute(AddProductParameterCommand(workspace, parameter))
workspace.command_manager.execute(AddProductParameterCommand(workspace, parameter_set))
workspace.command_manager.execute(AddProductMaterialCommand(workspace, material))
workspace.command_manager.execute(AssignProductMaterialCommand(workspace, part, material))
workspace.command_manager.execute(AddProductMechanicalMetadataCommand(workspace, metadata))

assert workspace.product_manager.parameters_for(part) == [parameter]
assert workspace.product_manager.parameter_sets_for(part) == [parameter_set]
assert workspace.product_manager.engineering_material_for(part) == material
assert workspace.product_manager.mechanical_metadata_for(part) == metadata

workspace.command_manager.undo()
assert workspace.product_manager.mechanical_metadata == []
workspace.command_manager.undo()
assert workspace.product_manager.engineering_material_for(part) is None
workspace.command_manager.redo()
assert workspace.product_manager.engineering_material_for(part) == material

print("3d-product-parameters-materials-commands-ok")

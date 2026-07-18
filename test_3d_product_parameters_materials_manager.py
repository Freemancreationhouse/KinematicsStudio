from engine.geometry import Vector3
from engine.product import (
    EngineeringMaterial,
    ManufacturingMetadata,
    MassProperties,
    MaterialCategory,
    MechanicalMetadata,
    MechanicalProperties,
    ParameterGroup,
    ParameterSet,
    PartParameter,
    ProductPart,
    ToleranceMetadata,
    FinishMetadata,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.product_manager.create_document("Parameters Product", "mm", 4)
part = workspace.product_manager.add_part(ProductPart("Parameterized Part", "mesh-parameter"))

group = workspace.product_manager.add_parameter_item(
    ParameterGroup("Dimensions", "Driving dimensions", part.id)
)
length = workspace.product_manager.add_parameter_item(
    PartParameter("Length", 120.0, "mm", "BaseLength", "Overall length", False, part.id, group.id)
)
parameter_set = workspace.product_manager.add_parameter_item(
    ParameterSet("Default Parameters", part.id, [length.id], [group.id])
)

workspace.product_manager.engineering_material_manager.ensure_default_categories()
steel_category = next(
    item for item in workspace.product_manager.material_categories
    if item.name == "Steel"
)
steel = workspace.product_manager.add_engineering_material_item(
    EngineeringMaterial("AISI 304", steel_category.id, 8000.0, color="#9e9e9e")
)
workspace.product_manager.engineering_material_manager.assign_material(part, steel)
metadata = workspace.product_manager.add_mechanical_metadata(
    MechanicalMetadata(
        part.id,
        MechanicalProperties(steel.id, 8000.0, 0.002, "Designed"),
        MassProperties(16.0, 0.002, 8000.0, Vector3(1.0, 2.0, 3.0), {"ix": 1.0}),
        ManufacturingMetadata("CNC Milling", "PN-001", "A", "Supplier", "Designed"),
        ToleranceMetadata("ISO 2768-m", "0.1mm"),
        FinishMetadata("Ra 1.6", "Anodized"),
    )
)

stats = workspace.product_manager.statistics()
parameter_stats = workspace.product_manager.parameter_manager.statistics()
material_stats = workspace.product_manager.engineering_material_manager.statistics()

assert workspace.product_manager.parameters_for(part) == [length]
assert workspace.product_manager.parameter_sets_for(part) == [parameter_set]
assert length.id in group.parameter_ids
assert parameter_set.id in part.parameter_set_ids
assert workspace.product_manager.engineering_material_for(part) == steel
assert workspace.product_manager.mechanical_metadata_for(part) == metadata
assert stats.parameters == 1
assert stats.parameter_sets == 1
assert stats.engineering_materials == 1
assert parameter_stats.parameters == 1
assert material_stats.materials == 1

print("3d-product-parameters-materials-manager-ok")

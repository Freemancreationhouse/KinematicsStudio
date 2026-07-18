import os
import tempfile

from engine.cad.application import CADApplication
from engine.product import (
    EngineeringMaterial,
    ManufacturingMetadata,
    MassProperties,
    MechanicalMetadata,
    MechanicalProperties,
    ParameterGroup,
    ParameterSet,
    PartParameter,
    ProductPart,
)


app = CADApplication()
workspace = app.workspace
workspace.product_manager.create_document("Persisted Batch B Product", "mm", 5)
part = workspace.product_manager.add_part(ProductPart("Persisted Parameter Part", "mesh-batch-b"))
group = workspace.product_manager.add_parameter_item(ParameterGroup("Identity", owner_id=part.id))
parameter = workspace.product_manager.add_parameter_item(
    PartParameter("Part Number", "PN-100", "", "", "Manufacturing part number", True, part.id, group.id)
)
workspace.product_manager.add_parameter_item(ParameterSet("Identity Set", part.id, [parameter.id], [group.id]))
material = workspace.product_manager.add_engineering_material_item(
    EngineeringMaterial("Titanium Grade 5", density=4430.0, color="#cfd8dc")
)
workspace.product_manager.engineering_material_manager.assign_material(part, material)
workspace.product_manager.add_mechanical_metadata(
    MechanicalMetadata(
        part.id,
        MechanicalProperties(material.id, 4430.0, 0.004),
        MassProperties(17.72, 0.004, 4430.0),
        ManufacturingMetadata("Additive Manufacturing", "PN-100", "B", "Supplier"),
    )
)
workspace.selection.select(part)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "product_batch_b.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    manager = restored_workspace.product_manager
    restored_part = manager.parts[0]

    assert manager.parameters[0].name == "Part Number"
    assert manager.parameters[0].read_only is True
    assert manager.parameter_sets[0].parameter_ids == [manager.parameters[0].id]
    assert manager.engineering_materials[0].name == "Titanium Grade 5"
    assert manager.engineering_material_for(restored_part).density == 4430.0
    assert manager.mechanical_metadata_for(restored_part).mass.mass == 17.72
    assert restored_part.selected is True

print("3d-product-parameters-materials-persistence-ok")

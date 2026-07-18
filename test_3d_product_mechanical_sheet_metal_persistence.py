import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import EngineeringMaterial, ProductPart, SolidBody


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(6.0, 3.0, 1.0), name="Persisted Mechanical Sheet Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Persisted Mechanical Sheet Product")
part = manager.add_part(ProductPart("Persisted Sheet Part", "Persisted Mechanical Sheet Mesh"))
body = manager.body_manager.add_item(SolidBody("Persisted Body", part.id, "Persisted Mechanical Sheet Mesh"))
material = manager.engineering_material_manager.add_item(EngineeringMaterial("Persisted Steel", density=7850.0))
library = manager.mechanical_library_manager.create_library("Persisted Library")
category = manager.mechanical_library_manager.create_category(library, "Bearings")
family = manager.mechanical_library_manager.create_family(library, category, "Deep Groove")
component = manager.mechanical_library_manager.create_component(library, category, family, part, "6202 Bearing")
rule = manager.sheet_metal_rule_manager.create_rule("Persisted Rule", material, 3.0, 1.5, 0.44)
manager.sheet_metal_rule_manager.create_gauge("3mm Steel", 3.0, material)
sheet_part = manager.sheet_metal_manager.convert_part(part, rule, "Persisted Sheet Metal")
sheet_body = manager.sheet_metal_manager.create_body(sheet_part, part, "Persisted Mechanical Sheet Mesh", body, "Edge Flange")
flat_pattern = manager.sheet_metal_manager.create_flat_pattern(sheet_part, sheet_body, "Persisted Flat Pattern")
workspace.selection.select(flat_pattern)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "mechanical_sheet_metal.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    assert restored.mechanical_libraries[0].name == "Persisted Library"
    assert restored.mechanical_library_categories[0].name == "Bearings"
    assert restored.mechanical_families[0].name == "Deep Groove"
    assert restored.mechanical_library_components[0].name == "6202 Bearing"
    assert restored.mechanical_library_components[0].product_part_id == restored.parts[0].id
    assert restored.mechanical_library_statistics.components == 1
    assert restored.sheet_metal_rules[0].thickness == 3.0
    assert restored.sheet_metal_rules[0].k_factor.value == 0.44
    assert restored.sheet_metal_gauges[0].thickness == 3.0
    assert restored.sheet_metal_parts[0].rule_id == restored.sheet_metal_rules[0].id
    assert restored.sheet_metal_bodies[0].metadata.operation == "Edge Flange"
    assert restored.flat_patterns[0].name == "Persisted Flat Pattern"
    assert restored.flat_patterns[0].selected is True
    assert restored.sheet_metal_statistics.flat_patterns == 1
    assert restored.sheet_metal_rule_statistics.rules == 1

print("3d-product-mechanical-sheet-metal-persistence-ok")

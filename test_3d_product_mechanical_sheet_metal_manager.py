from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import EngineeringMaterial, ProductPart, SolidBody
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(5.0, 2.0, 1.0), name="Mechanical Sheet Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Mechanical Sheet Product")
part = manager.add_part(ProductPart("Bracket Part", "Mechanical Sheet Mesh"))
body = manager.body_manager.add_item(SolidBody("Bracket Body", part.id, "Mechanical Sheet Mesh"))
material = manager.engineering_material_manager.add_item(EngineeringMaterial("Aluminium 6061", density=2700.0))

library = manager.mechanical_library_manager.create_library("Hardware Library")
category = manager.mechanical_library_manager.create_category(library, "Fasteners")
family = manager.mechanical_library_manager.create_family(library, category, "Socket Head Bolts")
standard = manager.mechanical_library_manager.create_standard("ISO", "ISO placeholder")
component = manager.mechanical_library_manager.create_component(
    library,
    category,
    family,
    part,
    "M6 Socket Head Bolt",
    standard,
)

rule = manager.sheet_metal_rule_manager.create_rule(
    "Aluminium Rule",
    material,
    thickness=2.0,
    inside_radius=1.0,
    k_factor=0.42,
)
gauge = manager.sheet_metal_rule_manager.create_gauge("2mm Aluminium", 2.0, material)
sheet_part = manager.sheet_metal_manager.convert_part(part, rule, "Bracket Sheet Metal")
sheet_body = manager.sheet_metal_manager.create_body(
    sheet_part,
    part,
    mesh_entity_id="Mechanical Sheet Mesh",
    body=body,
    operation="Base Flange",
)
flat_pattern = manager.sheet_metal_manager.create_flat_pattern(sheet_part, sheet_body)

mechanical_stats = manager.mechanical_library_manager.statistics()
sheet_stats = manager.sheet_metal_manager.statistics()
rule_stats = manager.sheet_metal_rule_manager.statistics()

assert mechanical_stats.libraries == 1
assert mechanical_stats.categories == 1
assert mechanical_stats.components == 1
assert mechanical_stats.families == 1
assert mechanical_stats.standards == 1
assert mechanical_stats.product_references == 1
assert component.product_part_id == part.id
assert component.id in library.component_ids
assert component.id in category.component_ids
assert component.id in family.component_ids
assert sheet_stats.parts == 1
assert sheet_stats.bodies == 1
assert sheet_stats.flat_patterns == 1
assert sheet_stats.operations == 1
assert rule_stats.rules == 1
assert rule_stats.gauges == 1
assert rule.material_id == material.id
assert rule.k_factor.value == 0.42
assert gauge.material_id == material.id
assert sheet_part.product_part_id == part.id
assert sheet_part.rule_id == rule.id
assert sheet_body.mesh_entity_id == "Mechanical Sheet Mesh"
assert sheet_body.body_id == body.id
assert flat_pattern.sheet_metal_part_id == sheet_part.id
assert sheet_part.flat_pattern_id == flat_pattern.id
assert len(workspace.scene3d.entities()) == 1
assert len(manager.dependency_edges) >= 5

print("3d-product-mechanical-sheet-metal-manager-ok")

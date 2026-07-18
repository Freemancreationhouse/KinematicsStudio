from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import PatternDefinition, ProductPart, SolidBody
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(10.0, 10.0, 10.0), name="Edge Pattern Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Edge Pattern Product")
part = manager.add_part(ProductPart("Edge Pattern Part", "Edge Pattern Mesh"))
body = manager.add_body_item(SolidBody("Edge Pattern Body", part.id, "Edge Pattern Mesh"))

fillet = manager.edge_modification_manager.create_fillet(part, body, [0, 1, 2], 2.5)
chamfer = manager.edge_modification_manager.create_chamfer(part, body, [3, 4], 1.25)
manager.feature_manager.apply_feature(fillet, workspace)
manager.feature_manager.apply_feature(chamfer, workspace)
pattern = manager.pattern_manager.create_pattern(
    part,
    body,
    source_features=[fillet, chamfer],
    pattern_definition=PatternDefinition(
        "Linear Pattern",
        [fillet.id, chamfer.id],
        [],
        5.0,
        3,
    ),
)
manager.pattern_manager.regenerate_pattern(pattern, workspace)

edge_stats = manager.edge_modification_manager.statistics()
pattern_stats = manager.pattern_manager.statistics()

assert fillet.type_name == "FilletFeature"
assert chamfer.type_name == "ChamferFeature"
assert len(manager.edge_modification_manager.selections_for_feature(fillet)) == 3
assert len(manager.edge_modification_manager.selections_for_feature(chamfer)) == 2
assert edge_stats.fillets == 1
assert edge_stats.chamfers == 1
assert pattern.type_name == "PatternFeature"
assert len(manager.pattern_manager.instances_for_feature(pattern)) == 6
assert pattern_stats.patterns == 1
assert pattern_stats.instances == 6
assert len(manager.dependency_edges) >= 4
assert mesh.primitive_type == "pattern"

print("3d-product-edge-pattern-manager-ok")

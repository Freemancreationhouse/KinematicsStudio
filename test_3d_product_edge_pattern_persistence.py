import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import PatternDefinition, ProductPart, SolidBody


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(8.0, 8.0, 8.0), name="Persisted Edge Pattern Mesh")
workspace.add_3d_entity(mesh)
manager = workspace.product_manager
manager.create_document("Persisted Edge Pattern Product")
part = manager.add_part(ProductPart("Persisted Edge Pattern Part", "Persisted Edge Pattern Mesh"))
body = manager.add_body_item(SolidBody("Persisted Edge Pattern Body", part.id, "Persisted Edge Pattern Mesh"))
fillet = manager.edge_modification_manager.create_fillet(part, body, [0, 1], 1.5)
chamfer = manager.edge_modification_manager.create_chamfer(part, body, [2], 0.75)
pattern = manager.pattern_manager.create_pattern(
    part,
    body,
    source_features=[fillet],
    pattern_definition=PatternDefinition("Mirror Pattern", [fillet.id], [], 2.0, 2),
)
manager.pattern_manager.regenerate_pattern(pattern, workspace)
workspace.selection.select(pattern)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "edge_pattern.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    assert restored.features[0].type_name == "FilletFeature"
    assert restored.features[1].type_name == "ChamferFeature"
    assert restored.features[2].type_name == "PatternFeature"
    assert len(restored.edge_selections) == 3
    assert restored.edge_modification_statistics.fillets == 1
    assert restored.pattern_definitions[0].pattern_type == "Mirror Pattern"
    assert len(restored.pattern_instances) == 2
    assert restored.features[2].selected is True

print("3d-product-edge-pattern-persistence-ok")

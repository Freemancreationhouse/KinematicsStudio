from engine.commands import EditProductFeatureCommand
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ExtrudeFeature, FeatureDefinition, FeatureOptions, ProductPart, Sketch, SolidBody
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
manager.create_document("Live Regeneration Product")

mesh_a = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Live Regen Mesh A")
mesh_b = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Live Regen Mesh B")
mesh_c = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Live Regen Mesh C")
workspace.add_3d_entity(mesh_a)
workspace.add_3d_entity(mesh_b)
workspace.add_3d_entity(mesh_c)

part_a = manager.add_part(ProductPart("Live Regen Part A", "Live Regen Mesh A"))
part_b = manager.add_part(ProductPart("Live Regen Part B", "Live Regen Mesh C"))
sketch_a = manager.add_sketch_item(Sketch("Live Regen Sketch A", part_a.id))
sketch_b = manager.add_sketch_item(Sketch("Live Regen Sketch B", part_a.id))
sketch_c = manager.add_sketch_item(Sketch("Live Regen Sketch C", part_b.id))
body_a = manager.add_body_item(SolidBody("Live Regen Body A", part_a.id, "Live Regen Mesh A"))
body_b = manager.add_body_item(SolidBody("Live Regen Body B", part_a.id, "Live Regen Mesh B"))
body_c = manager.add_body_item(SolidBody("Live Regen Body C", part_b.id, "Live Regen Mesh C"))

feature_a = manager.add_feature_item(
    ExtrudeFeature(
        "Live Regen Extrude A",
        part_a.id,
        FeatureDefinition(sketch_a.id, "", body_a.id, [body_a.id], FeatureOptions("Join", distance=2.0)),
    )
)
feature_b = manager.add_feature_item(
    ExtrudeFeature(
        "Live Regen Extrude B",
        part_a.id,
        FeatureDefinition(sketch_b.id, "", body_b.id, [body_b.id], FeatureOptions("Join", distance=4.0)),
    )
)
feature_c = manager.add_feature_item(
    ExtrudeFeature(
        "Live Regen Extrude C",
        part_b.id,
        FeatureDefinition(sketch_c.id, "", body_c.id, [body_c.id], FeatureOptions("Join", distance=6.0)),
    )
)

manager.feature_manager.apply_feature(feature_a, workspace)
manager.feature_manager.apply_feature(feature_b, workspace)
manager.feature_manager.apply_feature(feature_c, workspace)

workspace.selection.select(mesh_b)
scene_count = len(workspace.scene3d.entities())

workspace.command_manager.execute(EditProductFeatureCommand(workspace, feature_a, distance=8.0))

assert len(workspace.scene3d.entities()) == scene_count
assert mesh_a.parameters["distance"] == 8.0
assert mesh_b.parameters["distance"] == 4.0
assert mesh_c.parameters["distance"] == 6.0
assert manager.feature_editor.state_for(feature_a).dirty is False
assert manager.feature_editor.state_for(feature_b).dirty is False
assert feature_c.id not in [result.feature_id for result in manager.regeneration_results[-2:]]
assert workspace.selection.selected == [mesh_b]

workspace.command_manager.undo()

assert len(workspace.scene3d.entities()) == scene_count
assert mesh_a.parameters["distance"] == 2.0
assert mesh_b.parameters["distance"] == 4.0
assert mesh_c.parameters["distance"] == 6.0
assert manager.feature_editor.state_for(feature_a).dirty is True
assert manager.feature_editor.state_for(feature_b).dirty is True
assert workspace.selection.selected == [mesh_b]

print("3d-product-live-regeneration-incremental-ok")

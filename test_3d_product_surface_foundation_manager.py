from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import (
    ProductPart,
    SolidBody,
    SurfaceFeatureOptions,
    SurfaceFeatureDefinition,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(10.0, 1.0, 10.0), name="Surface Foundation Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Surface Foundation Product")
part = manager.add_part(ProductPart("Surface Foundation Part", "Surface Foundation Mesh"))
solid_body = manager.add_body_item(SolidBody("Surface Solid Body", part.id, "Surface Foundation Mesh"))
surface_body = manager.surface_manager.create_surface_body(
    part,
    "Surface Foundation Mesh",
    "Primary Surface",
)

loft_definition = SurfaceFeatureDefinition(
    "Loft Surface",
    target_surface_ids=[surface_body.id],
    options=SurfaceFeatureOptions(profile_ids=["profile-a", "profile-b"]),
)
loft = manager.feature_manager.create_feature("Loft Surface", part, body=surface_body, name="Loft Surface")
loft.surface_definition = loft_definition
manager.feature_manager.apply_feature(loft, workspace)

sweep = manager.feature_manager.create_feature("Sweep Surface", part, body=surface_body, name="Sweep Surface")
boundary = manager.feature_manager.create_feature("Boundary Surface", part, body=surface_body, name="Boundary Surface")
ruled = manager.feature_manager.create_feature("Ruled Surface", part, body=surface_body, name="Ruled Surface")
offset = manager.feature_manager.create_feature("Offset Surface", part, body=surface_body, name="Offset Surface")
fill = manager.feature_manager.create_feature("Fill Surface", part, body=surface_body, name="Fill Surface")

trim = manager.surface_operation_manager.create_operation("Trim", part, surface_body)
extend = manager.surface_operation_manager.create_operation("Extend", part, surface_body)
knit = manager.surface_operation_manager.create_operation("Knit", part, surface_body, targets=[surface_body], tools=[solid_body])
split = manager.surface_operation_manager.create_operation("Split", part, surface_body)

for feature in (sweep, boundary, ruled, offset, fill, trim, extend, knit, split):
    manager.feature_manager.apply_feature(feature, workspace)

surface_stats = manager.surface_manager.statistics()
operation_stats = manager.surface_operation_manager.statistics()

assert surface_body.type_name == "SurfaceBody"
assert surface_body.mesh_entity_id == "Surface Foundation Mesh"
assert len(manager.surface_bodies_for(part)) == 1
assert surface_stats.surface_bodies == 1
assert loft.type_name == "LoftSurfaceFeature"
assert sweep.type_name == "SweepSurfaceFeature"
assert boundary.type_name == "BoundarySurfaceFeature"
assert ruled.type_name == "RuledSurfaceFeature"
assert offset.type_name == "OffsetSurfaceFeature"
assert fill.type_name == "FillSurfaceFeature"
assert trim.type_name == "TrimSurfaceFeature"
assert extend.type_name == "ExtendSurfaceFeature"
assert knit.type_name == "KnitSurfaceFeature"
assert split.type_name == "SplitSurfaceFeature"
assert operation_stats.trim == 1
assert operation_stats.extend == 1
assert operation_stats.knit == 1
assert operation_stats.split == 1
assert len(manager.dependency_edges) >= 4
assert mesh.primitive_type == "split surface"

print("3d-product-surface-foundation-manager-ok")

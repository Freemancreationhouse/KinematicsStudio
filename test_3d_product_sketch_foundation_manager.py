from engine.geometry import Vector3
from engine.product import (
    Centerline,
    Constraint,
    ConstraintGroup,
    DimensionMetadata,
    Sketch,
    SketchCircle,
    SketchDimension,
    SketchLine,
    SketchPlane,
    SketchProfile,
    ProductPart,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
manager.create_document("Sketch Product", "mm", 3)
part = manager.add_part(ProductPart("Sketch Part", "mesh-sketch", location=Vector3()))
plane = manager.add_sketch_item(SketchPlane("Front Plane"))
sketch = manager.sketch_manager.create_sketch("Base Sketch", part, plane)
profile = manager.add_sketch_item(SketchProfile("Base Profile", sketch.id))
line = manager.add_sketch_item(
    SketchLine("Profile Line", sketch.id, Vector3(), Vector3(10.0, 0.0, 0.0))
)
circle = manager.add_sketch_item(SketchCircle("Bolt Circle", sketch.id, Vector3(3.0, 3.0, 0.0), 1.5))
centerline = manager.add_sketch_item(Centerline("Horizontal Centerline", sketch.id))
constraint_group = manager.add_sketch_constraint_item(ConstraintGroup("Shape Constraints", sketch.id))
constraint = manager.add_sketch_constraint_item(
    Constraint("Horizontal", sketch.id, [line.id], metadata=None)
)
dimension = manager.add_sketch_dimension_item(
    SketchDimension(
        "Linear",
        10.0,
        "mm",
        sketch.id,
        [line.id],
        metadata=DimensionMetadata(expression="Length"),
    )
)

manager.sketch_manager.activate(sketch)
stats = manager.statistics()
sketch_stats = manager.sketch_manager.statistics()
constraint_stats = manager.constraint_manager.statistics()
dimension_stats = manager.dimension_manager.statistics()

assert sketch.id in part.sketch_ids
assert profile.id in sketch.profile_ids
assert line.id in sketch.geometry_ids
assert circle.id in sketch.geometry_ids
assert centerline.id in sketch.geometry_ids
assert constraint.id in sketch.constraint_ids
assert dimension.id in sketch.dimension_ids
assert manager.sketches_for(part) == [sketch]
assert len(manager.geometry_for_sketch(sketch)) == 3
assert manager.constraints_for_sketch(sketch) == [constraint]
assert manager.dimensions_for_sketch(sketch) == [dimension]
assert manager.active_sketch_id == sketch.id
assert sketch.active is True
assert stats.sketches == 1
assert stats.sketch_geometry == 3
assert stats.sketch_constraints == 1
assert stats.sketch_dimensions == 1
assert sketch_stats.construction_geometry == 1
assert constraint_stats.groups == 1
assert dimension_stats.driving == 1

print("3d-product-sketch-foundation-manager-ok")

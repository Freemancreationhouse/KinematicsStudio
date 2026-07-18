import os
import tempfile

from engine.cad.application import CADApplication
from engine.geometry import Vector3
from engine.product import (
    Constraint,
    DimensionMetadata,
    ProductPart,
    Sketch,
    SketchDimension,
    SketchLine,
    SketchPlane,
    SketchRectangle,
)


app = CADApplication()
workspace = app.workspace
manager = workspace.product_manager
manager.create_document("Persisted Sketch Product", "mm", 4)
part = manager.add_part(ProductPart("Persisted Sketch Part", "mesh-persisted-sketch"))
plane = manager.add_sketch_item(SketchPlane("Top Plane"))
sketch = manager.add_sketch_item(Sketch("Persisted Sketch", part.id, plane.id, location=Vector3(1.0, 2.0, 0.0)))
line = manager.add_sketch_item(SketchLine("Persisted Line", sketch.id, Vector3(), Vector3(7.0, 0.0, 0.0)))
rectangle = manager.add_sketch_item(SketchRectangle("Persisted Rectangle", sketch.id, Vector3(), Vector3(2.0, 3.0, 0.0)))
manager.add_sketch_constraint_item(Constraint("Parallel", sketch.id, [line.id, rectangle.id]))
manager.add_sketch_dimension_item(
    SketchDimension("Linear", 7.0, "mm", sketch.id, [line.id], metadata=DimensionMetadata(expression="Length"))
)
manager.sketch_manager.activate(sketch)
workspace.selection.select(sketch)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "product_sketch.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager
    restored_sketch = restored.sketches[0]

    assert restored.active_sketch_id == restored_sketch.id
    assert restored.parts[0].sketch_ids == [restored_sketch.id]
    assert len(restored.sketch_geometry) == 2
    assert restored.sketch_geometry[1].type_name == "SketchRectangle"
    assert restored.sketch_constraints[0].constraint_type == "Parallel"
    assert restored.sketch_dimensions[0].metadata.expression == "Length"
    assert restored_sketch.selected is True

print("3d-product-sketch-foundation-persistence-ok")

import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ComputedParameter, GlobalParameter, ParameterCategory, ProductPart


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(3.0, 2.0, 1.0), name="Persisted Parameter Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
document = manager.create_document("Persisted Parameter Product")
part = manager.add_part(ProductPart("Persisted Parameter Part", "Persisted Parameter Mesh"))
category = manager.parameter_manager.add_item(ParameterCategory("Persisted Category", "Length"))
width = manager.parameter_manager.add_item(GlobalParameter("Persisted Width", 10.0, parameter_type="Length", unit="mm", owner_id=document.id, category_id=category.id))
height = manager.parameter_manager.create_parameter("Persisted Height", 5.0, "Length", part, "Local", unit="mm", category=category)
area = manager.parameter_manager.add_item(ComputedParameter("Persisted Area", 0.0, parameter_type="Area", unit="mm^2", owner_id=part.id, category_id=category.id))
expression = manager.parameter_manager.create_expression("Persisted Expression", "Persisted Width * Persisted Height", area, [width, height], [part], unit="mm^2")
binding = manager.parameter_manager.bind_parameter(width, area, "ParameterToExpression", expression)
workspace.selection.select(area)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "parametric_parameters.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    assert restored.parameter_categories[0].name == "Persisted Category"
    assert restored.parameters[0].name == "Persisted Width"
    assert restored.parameters[0].scope == "Global"
    assert restored.parameters[1].scope == "Local"
    assert restored.parameters[2].scope == "Computed"
    assert restored.parameters[2].selected is True
    assert restored.expressions[0].text == "Persisted Width * Persisted Height"
    assert restored.expressions[0].evaluation_state == "Not Evaluated"
    assert restored.expression_bindings[0].id == binding.id
    assert restored.parameter_statistics.parameters == 3
    assert restored.expression_statistics.bindings == 1
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-parametric-parameters-persistence-ok")

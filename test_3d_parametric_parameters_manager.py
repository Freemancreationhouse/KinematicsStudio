from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import (
    ComputedParameter,
    ExpressionReference,
    ExpressionTree,
    GlobalParameter,
    ParameterCategory,
    ParametricContext,
    ProductPart,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(2.0, 2.0, 2.0), name="Parameter Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
product_document = manager.create_document("Parameter Product")
part = manager.add_part(ProductPart("Parameter Part", "Parameter Mesh"))
engine = manager.parametric_manager.create_engine("Parameter Engine")
context = ParametricContext(product_document_id=product_document.id, product_part_id=part.id, mesh_entity_id=mesh.name)
parametric_document = manager.parametric_manager.create_document("Parameter Parametric Document", engine, context, [part])

category = manager.parameter_manager.add_item(ParameterCategory("Driving Parameters", "Length"))
global_parameter = manager.parameter_manager.add_item(
    GlobalParameter(
        "Global Width",
        120.0,
        parameter_type="Length",
        unit="mm",
        owner_id=product_document.id,
        category_id=category.id,
    )
)
local_parameter = manager.parameter_manager.create_parameter(
    "Local Height",
    75.0,
    "Length",
    part,
    "Local",
    unit="mm",
    category=category,
)
computed_parameter = manager.parameter_manager.add_item(
    ComputedParameter(
        "Computed Area",
        0.0,
        parameter_type="Area",
        unit="mm^2",
        owner_id=part.id,
        category_id=category.id,
    )
)
expression = manager.parameter_manager.create_expression(
    "Area Expression",
    "Global Width * Local Height",
    computed_parameter,
    [global_parameter, local_parameter],
    [part],
    unit="mm^2",
)
binding = manager.parameter_manager.bind_parameter(global_parameter, computed_parameter, "ParameterToParameter", expression)
tree = manager.parameter_manager.add_item(ExpressionTree(expression.id, ["future-node-placeholder"], [global_parameter.id]))
reference = manager.parameter_manager.add_item(ExpressionReference(expression.id, [global_parameter.id, local_parameter.id], [part.id]))

stats = manager.parameter_manager.statistics()

assert parametric_document.reference_ids == [part.id]
assert category.parameter_ids == [global_parameter.id, local_parameter.id, computed_parameter.id]
assert computed_parameter.expression_id == expression.id
assert binding.id in global_parameter.binding_ids
assert binding.id in expression.binding_ids
assert tree.expression_id == expression.id
assert reference.parameter_ids == [global_parameter.id, local_parameter.id]
assert stats.parameters == 3
assert stats.categories == 1
assert stats.expressions == 1
assert stats.bindings == 1
assert stats.global_parameters == 1
assert stats.local_parameters == 1
assert stats.computed_parameters == 1
assert manager.expression_statistics.trees == 1
assert manager.expression_statistics.references == 1
assert len(manager.dependency_edges) >= 5
assert expression.evaluation_state == "Not Evaluated"
assert len(workspace.scene3d.entities()) == 1

print("3d-parametric-parameters-manager-ok")

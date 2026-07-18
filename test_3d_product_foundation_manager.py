from engine.entities import MeshEntity
from engine.geometry import MeshData, Vector3
from engine.product import (
    Component,
    ComponentCategory,
    ComponentMetadata,
    ComponentType,
    ProductMetadata,
    ProductPart,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
document = workspace.product_manager.create_document(
    "Product Foundation",
    "mm",
    4,
    ProductMetadata("Single and multi part foundation", "Studio", "Aluminum"),
)

mesh = MeshEntity(MeshData.box(10.0, 5.0, 2.0), name="Housing Mesh")
mesh.id = "housing-mesh"
workspace.add_3d_entity(mesh)

part = ProductPart(
    "Housing",
    mesh.id,
    ProductMetadata("Machined housing", "Studio", "Aluminum"),
    Vector3(1.0, 2.0, 3.0),
)
part.mesh_entity_name = mesh.name
workspace.product_manager.add_part(part)

workspace.product_manager.component_manager.ensure_default_categories()
category = workspace.product_manager.add_component_item(
    ComponentCategory("Custom Parts", "Custom manufactured components", "#81c784")
)
component_type = workspace.product_manager.add_component_item(
    ComponentType("Housing Type", category.id)
)
component = workspace.product_manager.add_component_item(
    Component(
        "Housing Component",
        part.id,
        component_type.id,
        category.id,
        ComponentMetadata("Product component", "Studio Kinematics", "H-001"),
    )
)

stats = workspace.product_manager.statistics()

assert document in workspace.product_manager.documents
assert part.id in document.part_ids
assert component.id in part.component_ids
assert workspace.product_manager.components_for(part) == [component]
assert workspace.product_manager.component_type_for(component) == component_type
assert workspace.product_manager.component_category_for(component).name == "Custom Parts"
assert stats.documents == 1
assert stats.parts == 1
assert stats.components == 1
assert workspace.visible_product_objects() == [part, component]
assert part.segments()

print("3d-product-foundation-manager-ok")

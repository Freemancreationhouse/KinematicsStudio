import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData, Vector3
from engine.product import Component, ComponentCategory, ComponentType, ProductMetadata, ProductPart


app = CADApplication()
workspace = app.workspace
workspace.product_manager.create_document("Persisted Product", "inch", 5)

mesh = MeshEntity(MeshData.box(4.0, 2.0, 1.0), name="Persisted Mesh")
mesh.id = "persisted-mesh"
workspace.add_3d_entity(mesh)

part = ProductPart(
    "Persisted Part",
    mesh.id,
    ProductMetadata("Persisted part", "Studio", "Steel"),
    Vector3(3.0, 2.0, 1.0),
)
part.mesh_entity_name = mesh.name
workspace.product_manager.add_part(part)
category = workspace.product_manager.add_component_item(ComponentCategory("Standard Parts"))
component_type = workspace.product_manager.add_component_item(ComponentType("Fastener", category.id))
component = workspace.product_manager.add_component_item(
    Component("Fastener Component", part.id, component_type.id, category.id)
)
workspace.selection.select(part)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "product_batch_a.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    manager = restored_workspace.product_manager
    restored_part = manager.parts[0]

    assert manager.active_document.name == "Persisted Product"
    assert manager.active_document.units == "inch"
    assert restored_part.name == "Persisted Part"
    assert restored_part.mesh_entity_id == "persisted-mesh"
    assert getattr(restored_part, "entity", None).name == "Persisted Mesh"
    assert manager.components[0].name == component.name
    assert manager.component_type_for(manager.components[0]).name == "Fastener"
    assert restored_part.selected is True

print("3d-product-foundation-persistence-ok")

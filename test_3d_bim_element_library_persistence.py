import os
import tempfile

from engine.bim import (
    BIMCategory,
    BIMElementDefinition,
    BIMInstance,
    BIMType,
    ElementCategoryMetadata,
    ElementParameters,
    ElementRelationships,
)
from engine.cad.application import CADApplication
from engine.entities.entity3d import MeshEntity
from engine.geometry import MeshData


app = CADApplication()
workspace = app.workspace
workspace.bim_manager.create_project("Persisted Element BIM")
category = workspace.bim_manager.add_category(BIMCategory("Windows"))
element_category = workspace.bim_manager.add_element_category(
    ElementCategoryMetadata("Window", "Window elements", "#81d4fa")
)
definition = workspace.bim_manager.add_element_definition(
    BIMElementDefinition(
        "Window",
        "Window Element",
        element_category.id,
        parameters=ElementParameters("Window", "External window", "Window", "Fixed", "Aluminum", "30min"),
    )
)
bim_type = BIMType("Fixed Window", category.id)
bim_type.element_definition_id = definition.id
workspace.bim_manager.add_type(bim_type)
mesh = MeshEntity(MeshData.box(1.2, 0.1, 1.0), name="Persisted Element Window Mesh")
mesh.id = "persisted-element-window-mesh"
workspace.add_3d_entity(mesh)
instance = BIMInstance("Persisted Element Window", category.id, bim_type.id, mesh)
instance.element_definition_id = definition.id
instance.element_parameters.model = "WIN-A"
instance.element_relationships = ElementRelationships(hosts=["wall-a"], adjacent=["space-a"])
workspace.bim_manager.add_instance(instance)
workspace.selection.select(instance)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "bim_element_library.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored_project = restored_workspace.bim_manager.active_project
    restored_definition = restored_project.element_definitions[0]
    restored_instance = restored_project.instances[0]
    stats = restored_workspace.bim_manager.element_library.statistics()
    resolved = restored_workspace.bim_manager.resolved_instance_properties(restored_instance)

    assert restored_project.element_categories[0].name == "Window"
    assert restored_definition.kind == "Window"
    assert restored_instance.element_definition_id == restored_definition.id
    assert restored_instance.entity is not None
    assert restored_instance.selected is True
    assert restored_instance.element_relationships.hosts == ["wall-a"]
    assert resolved["material"] == "Aluminum"
    assert resolved["model"] == "WIN-A"
    assert stats.instances == 1

print("3d-bim-element-library-persistence-ok")

from engine.bim import (
    BIMCategory,
    BIMElementDefinition,
    BIMFamily,
    BIMInstance,
    BIMType,
    ElementCategoryMetadata,
    ElementMetadata,
    ElementParameters,
    ElementRelationships,
)
from engine.entities.entity3d import MeshEntity
from engine.geometry import MeshData
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.bim_manager.create_project("Element Library BIM")
category = workspace.bim_manager.add_category(BIMCategory("Walls", color="#ffcc80"))
element_category = workspace.bim_manager.add_element_category(
    ElementCategoryMetadata("Wall", "Wall elements", "#ffcc80", {"ifc": "IfcWall"})
)
wall_definition = workspace.bim_manager.add_element_definition(
    BIMElementDefinition(
        "Wall",
        "Basic Wall Element",
        element_category.id,
        ElementMetadata("Wall metadata", "Concrete", "2h"),
        ElementParameters(
            "Basic Wall",
            "Load-bearing wall",
            "Wall",
            "200mm",
            "Concrete",
            "2h",
            "U-0.30",
            "STC 50",
            True,
            True,
            "Studio",
            "W200",
            "100",
            {"ifc": "IfcWall"},
            {"Phase": "New"},
        ),
    )
)
family = workspace.bim_manager.add_family(BIMFamily("Wall Family", category.id))
bim_type = BIMType("200mm Wall", category.id)
bim_type.family_id = family.id
bim_type.element_definition_id = wall_definition.id
workspace.bim_manager.add_type(bim_type)
mesh = MeshEntity(MeshData.box(2.0, 0.2, 3.0), name="Element Wall Mesh")
mesh.id = "element-wall-mesh"
workspace.add_3d_entity(mesh)
instance = BIMInstance("Element Wall", category.id, bim_type.id, mesh)
instance.family_id = family.id
instance.element_definition_id = wall_definition.id
instance.element_parameters.material = "Concrete"
instance.element_relationships = ElementRelationships(hosts=["level-1"], adjacent=["space-1"])
workspace.bim_manager.add_instance(instance)

stats = workspace.bim_manager.element_library.statistics()
resolved = workspace.bim_manager.resolved_instance_properties(instance)

assert workspace.bim_manager.element_library.get_definition("Wall") is wall_definition
assert stats.definitions == 1
assert stats.categories == 1
assert stats.instances == 1
assert stats.relationships == 2
assert resolved["material"] == "Concrete"
assert resolved["load_bearing"] is True
assert workspace.bim_manager.element_category_for(instance) is element_category

print("3d-bim-element-library-manager-ok")

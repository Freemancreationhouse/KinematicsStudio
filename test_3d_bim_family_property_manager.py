from engine.bim import (
    BIMCategory,
    BIMFamily,
    BIMInstance,
    BIMType,
    FamilyCategory,
    FamilyMetadata,
    PropertyDefinition,
    PropertyGroup,
    PropertySet,
    PropertyValue,
)
from engine.entities.entity3d import MeshEntity
from engine.geometry import MeshData
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.bim_manager.create_project("Family BIM")
category = workspace.bim_manager.add_category(BIMCategory("Walls", color="#ef9a9a"))
family_category = workspace.bim_manager.add_family_category(
    FamilyCategory("Basic Wall Families", category.id)
)
family = workspace.bim_manager.add_family(
    BIMFamily("Basic Wall Family", category.id, FamilyMetadata("Author", "Factory"))
)
bim_type = BIMType("200mm Wall", category.id)
bim_type.family_id = family.id
bim_type.type_parameters.values["FireRating"] = "2h"
bim_type.type_defaults.values["Height"] = 3.0
workspace.bim_manager.add_type(bim_type)

property_set = PropertySet("Pset_WallCommon", family.id, "Pset_WallCommon", {"ifc": "IfcWall"})
definition = PropertyDefinition("Reference", "Text", "", "Wall reference", "Reference")
property_set.add_property(definition, PropertyValue(definition.id, "W-001", "IFC"))
property_set.groups.append(PropertyGroup("Identity", [definition.id]))
workspace.bim_manager.add_property_set(property_set)

mesh = MeshEntity(MeshData.box(2.0, 0.2, 3.0), name="Family Wall Mesh")
mesh.id = "family-wall-mesh"
workspace.add_3d_entity(mesh)
instance = BIMInstance("Family Wall Instance", category.id, bim_type.id, mesh)
instance.family_id = family.id
instance.instance_parameters.values["Mark"] = "W-101"
instance.instance_overrides.values["Height"] = 3.4
workspace.bim_manager.add_instance(instance)

family.refresh_statistics(workspace.bim_manager.active_project)
resolved = workspace.bim_manager.resolved_instance_properties(instance)
browser = workspace.bim_manager.project_browser()

assert family_category.name == "Basic Wall Families"
assert workspace.bim_manager.family_library.get_family("Basic Wall Family") is family
assert family.statistics.types == 1
assert family.statistics.instances == 1
assert family.statistics.property_sets == 1
assert property_set.value_for("Reference").value == "W-001"
assert resolved["Height"] == 3.4
assert resolved["Mark"] == "W-101"
assert browser["sites"] == []
assert workspace.bim_manager.property_sets_for(family)[0] is property_set

print("3d-bim-family-property-manager-ok")

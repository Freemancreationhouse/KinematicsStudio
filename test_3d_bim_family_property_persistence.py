import os
import tempfile

from engine.bim import (
    BIMCategory,
    BIMFamily,
    BIMInstance,
    BIMType,
    FamilyCategory,
    PropertyDefinition,
    PropertySet,
    PropertyValue,
)
from engine.cad.application import CADApplication
from engine.entities.entity3d import MeshEntity
from engine.geometry import MeshData


app = CADApplication()
workspace = app.workspace
workspace.bim_manager.create_project("Persisted Family BIM")
category = workspace.bim_manager.add_category(BIMCategory("Windows"))
workspace.bim_manager.add_family_category(FamilyCategory("Window Families", category.id))
family = workspace.bim_manager.add_family(BIMFamily("Window Family", category.id))
bim_type = BIMType("Fixed Window", category.id)
bim_type.family_id = family.id
bim_type.type_defaults.values["SillHeight"] = 0.9
workspace.bim_manager.add_type(bim_type)

mesh = MeshEntity(MeshData.box(1.2, 0.1, 1.0), name="Persisted Window Mesh")
mesh.id = "persisted-window-mesh"
workspace.add_3d_entity(mesh)
instance = BIMInstance("Persisted Window", category.id, bim_type.id, mesh)
instance.family_id = family.id
instance.instance_overrides.values["SillHeight"] = 1.0
workspace.bim_manager.add_instance(instance)
workspace.selection.select(instance)

property_set = PropertySet("Pset_WindowCommon", instance.id, "Pset_WindowCommon")
definition = PropertyDefinition("Reference", "Text")
property_set.add_property(definition, PropertyValue(definition.id, "WIN-01", "IFC"))
workspace.bim_manager.add_property_set(property_set)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "bim_family_property.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored_project = restored_workspace.bim_manager.active_project
    restored_family = restored_project.families[0]
    restored_type = restored_project.types[0]
    restored_instance = restored_project.instances[0]
    restored_set = restored_project.property_sets[0]
    resolved = restored_workspace.bim_manager.resolved_instance_properties(restored_instance)

    assert restored_family.name == "Window Family"
    assert restored_type.family_id == restored_family.id
    assert restored_instance.family_id == restored_family.id
    assert restored_instance.entity is not None
    assert restored_instance.selected is True
    assert restored_set.value_for("Reference").value == "WIN-01"
    assert resolved["SillHeight"] == 1.0
    assert resolved["Reference"] == "WIN-01"

print("3d-bim-family-property-persistence-ok")

import os
import tempfile

from engine.bim import BIMCategory, BIMInstance, BIMSettings, BIMType, Building, GridSystem, Level, Site
from engine.cad.application import CADApplication
from engine.entities.entity3d import MeshEntity
from engine.geometry import MeshData, Vector3


app = CADApplication()
workspace = app.workspace
workspace.bim_manager.create_project("Persisted BIM", settings=BIMSettings("meters", 3.6, 7.5))
site = workspace.bim_manager.add_site(Site("Persisted Site", Vector3(1.0, 2.0, 0.0)))
building = workspace.bim_manager.add_building(Building("Persisted Building", site.id))
level = workspace.bim_manager.add_level(Level("Persisted Level", 4.0, 3.6, building.id))
grid = workspace.bim_manager.add_grid(GridSystem("Persisted Grid", building.id, 7.5, 3, 3, 4.0))
category = workspace.bim_manager.add_category(BIMCategory("Doors"))
bim_type = workspace.bim_manager.add_type(BIMType("Door Type", category.id))
mesh = MeshEntity(MeshData.box(1.0, 0.1, 2.1), name="Persisted Door Mesh")
mesh.id = "persisted-door-mesh"
workspace.add_3d_entity(mesh)
instance = BIMInstance("Persisted Door", category.id, bim_type.id, mesh)
instance.level_id = level.id
instance.building_id = building.id
instance.property_sets["Identity"] = {"Mark": "D-001"}
workspace.bim_manager.add_instance(instance)
workspace.selection.select(instance)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "bim_foundation.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored_project = restored_workspace.bim_manager.active_project
    restored_instance = restored_project.instances[0]

    assert restored_project.name == "Persisted BIM"
    assert restored_project.settings.grid_spacing == 7.5
    assert restored_project.sites[0].name == "Persisted Site"
    assert restored_project.buildings[0].name == "Persisted Building"
    assert restored_project.levels[0].name == "Persisted Level"
    assert restored_project.grids[0].name == "Persisted Grid"
    assert restored_instance.name == "Persisted Door"
    assert restored_instance.property_sets["Identity"]["Mark"] == "D-001"
    assert restored_instance.entity is not None
    assert restored_instance.selected is True

print("3d-bim-foundation-persistence-ok")

from engine.bim import (
    BIMCategory,
    BIMInstance,
    BIMSettings,
    BIMType,
    Building,
    BuildingMetadata,
    GridSystem,
    Level,
    Site,
)
from engine.entities.entity3d import MeshEntity
from engine.geometry import MeshData, Vector3
from engine.workspace.workspace import Workspace


workspace = Workspace()
project = workspace.bim_manager.create_project(
    "BIM Foundation",
    BuildingMetadata("Author", "Studio", "KS-1200", "Site Address", "Design"),
    BIMSettings("meters", 4.0, 8.0, "Architecture", "OmniClass"),
)
site = workspace.bim_manager.add_site(Site("Main Site", Vector3(10.0, 20.0, 0.0)))
building = workspace.bim_manager.add_building(Building("Tower A", site.id))
level = workspace.bim_manager.add_level(Level("Level 01", 0.0, 4.0, building.id))
grid = workspace.bim_manager.add_grid(GridSystem("Grid A", building.id, 8.0, 4, 3, 0.0))
category = workspace.bim_manager.add_category(BIMCategory("Walls", "Architecture", "Wall objects", "#90caf9"))
bim_type = workspace.bim_manager.add_type(BIMType("Basic Wall", category.id, {"width": 0.2}, {"code": "A-WALL"}))

mesh = MeshEntity(MeshData.box(2.0, 0.2, 3.0), name="Wall Mesh")
mesh.id = "wall-mesh"
workspace.add_3d_entity(mesh)
instance = BIMInstance("Wall Instance", category.id, bim_type.id, mesh)
instance.level_id = level.id
instance.building_id = building.id
instance.property_sets["Identity"] = {"Mark": "W-001"}
instance.relationships["hosted_by"] = level.id
workspace.bim_manager.add_instance(instance)

browser = workspace.bim_manager.project_browser()

assert project in workspace.bim_manager.projects
assert browser["project"] == "BIM Foundation"
assert browser["sites"][0]["buildings"][0]["levels"][0]["name"] == "Level 01"
assert browser["sites"][0]["buildings"][0]["grids"][0]["name"] == "Grid A"
assert browser["sites"][0]["buildings"][0]["objects"][0]["name"] == "Wall Instance"
assert instance.guid
assert instance.property_sets["Identity"]["Mark"] == "W-001"
assert workspace.visible_bim_objects() == [level, grid, instance]
assert level.segments()
assert grid.segments()
assert len(instance.segments()) == len(mesh.segments())

print("3d-bim-foundation-manager-ok")

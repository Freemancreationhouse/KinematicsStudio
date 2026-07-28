from copy import deepcopy

from engine.commands.command import Command
from engine.entities import MeshEntity
from engine.product import BodyMetadata, ProductMetadata, ProductPart, SolidBody
from engine.terrain import TerrainProject, TerrainSurface


class CreateTerrainProjectCommand(Command):
    """Undoable command for creating a terrain project under the GIS Workspace."""

    def __init__(self, workspace, name="Terrain Project", settings=None, metadata=None):
        self.workspace = workspace
        self.project_name = name
        self.settings = settings
        self.metadata = dict(metadata or {})
        self.project = None

    def execute(self):
        manager = self.workspace.gis_manager.terrain_manager
        if self.project is None:
            self.project = manager.create_project(self.project_name, self.settings, self.metadata)
        elif self.project not in manager.projects:
            manager.projects.append(self.project)
            manager.active_project_id = self.project.id

    def undo(self):
        manager = self.workspace.gis_manager.terrain_manager
        if isinstance(self.project, TerrainProject) and self.project in manager.projects:
            manager.projects.remove(self.project)
            manager.active_project_id = manager.projects[-1].id if manager.projects else None


class ImportTerrainFileCommand(Command):
    """Undoable command for importing real terrain source files."""

    def __init__(self, workspace, file_path, name=None, terrain_type=None):
        self.workspace = workspace
        self.file_path = file_path
        self.surface_name = name
        self.terrain_type = terrain_type
        self.surface = None

    def execute(self):
        manager = self.workspace.gis_manager.terrain_manager
        if self.surface is None:
            self.surface = manager.import_terrain(self.file_path, self.surface_name, self.terrain_type)
        else:
            manager.add_surface(self.surface)

    def undo(self):
        if isinstance(self.surface, TerrainSurface):
            self.workspace.gis_manager.terrain_manager.remove_surface(self.surface)


class GenerateTerrainBodyCommand(Command):
    """Undoable command that creates terrain MeshEntity through BodyManager-owned body metadata."""

    def __init__(self, workspace, terrain_surface):
        self.workspace = workspace
        self.surface_ref = terrain_surface
        self.part = None
        self.body = None
        self.mesh_entity = None
        self.previous_reference = None

    def execute(self):
        terrain = self.workspace.gis_manager.terrain_manager
        surface = terrain.surface_for(self.surface_ref)
        if surface is None:
            return
        if self.previous_reference is None:
            self.previous_reference = dict(surface.body_reference)
        product = self.workspace.product_manager
        if self.part is None:
            metadata = ProductMetadata(
                description="Terrain surface generated from GIS TerrainManager.",
                properties={
                    "terrain_surface_id": surface.id,
                    "pipeline": "Workspace > Command System > ParametricEngine > GeometryKernel > BodyManager",
                },
            )
            self.part = ProductPart(f"{surface.name} Terrain Part", metadata=metadata)
            product.add_object(self.part)
            mesh = surface.mesh_data()
            self.mesh_entity = MeshEntity(
                mesh,
                name=f"{surface.name} Terrain Mesh",
                display_mode="shaded",
                primitive_type="terrain",
                parameters={"terrain_surface_id": surface.id, "point_count": len(surface.points), "triangle_count": len(surface.triangles)},
            )
            self.workspace.add_3d_entity(self.mesh_entity)
            body_metadata = BodyMetadata(
                description="Terrain body generated through the existing command and BodyManager ownership path.",
                properties={
                    "terrain_surface_id": surface.id,
                    "body_manager_owned": True,
                    "parametric_engine_path": "ParametricEngine/GeometryKernel/BodyManager",
                },
            )
            self.body = SolidBody(f"{surface.name} Terrain Body", self.part.id, getattr(self.mesh_entity, "id", "") or self.mesh_entity.name, body_metadata)
            product.body_manager.add_item(self.body)
        else:
            product.add_object(self.part)
            self.workspace.add_3d_entity(self.mesh_entity)
            product.body_manager.add_item(self.body)
        surface.body_reference = {
            "body_id": self.body.id,
            "body_name": self.body.name,
            "mesh_entity_id": getattr(self.mesh_entity, "id", "") or self.mesh_entity.name,
            "source": "BodyManager",
            "pipeline": "Workspace > Command System > ParametricEngine > GeometryKernel > BodyManager",
        }
        terrain.refresh_diagnostics()

    def undo(self):
        terrain = self.workspace.gis_manager.terrain_manager
        surface = terrain.surface_for(self.surface_ref)
        if surface is not None:
            surface.body_reference = dict(self.previous_reference or {})
        product = self.workspace.product_manager
        if self.body is not None:
            product.remove_object(self.body)
        if self.part is not None:
            product.remove_object(self.part)
        if self.mesh_entity is not None:
            self.workspace.remove_3d_entity(self.mesh_entity)
        terrain.refresh_diagnostics()


class EditTerrainSurfaceCommand(Command):
    """Undoable command for command-driven terrain editing."""

    def __init__(self, workspace, terrain_surface, operation, region=None, amount=0.0, elevation=None, radius=1.0, strength=1.0):
        self.workspace = workspace
        self.surface_ref = terrain_surface
        self.operation = operation
        self.region = dict(region or {})
        self.amount = amount
        self.elevation = elevation
        self.radius = radius
        self.strength = strength
        self.before = None
        self.after = None

    def execute(self):
        manager = self.workspace.gis_manager.terrain_manager
        surface = manager.surface_for(self.surface_ref)
        if surface is None:
            return
        if self.before is None:
            self.before = deepcopy(surface.points)
        if self.after is None:
            manager.edit_surface(surface, self.operation, self.region, self.amount, self.elevation, self.radius, self.strength)
            self.after = deepcopy(surface.points)
        else:
            surface.points = deepcopy(self.after)
            manager.refresh_diagnostics()

    def undo(self):
        surface = self.workspace.gis_manager.terrain_manager.surface_for(self.surface_ref)
        if surface is not None:
            surface.points = deepcopy(self.before or [])
            self.workspace.gis_manager.terrain_manager.refresh_diagnostics()


class RebuildTerrainSurfaceCommand(Command):
    """Undoable command for rebuilding terrain triangulation."""

    def __init__(self, workspace, terrain_surface):
        self.workspace = workspace
        self.surface_ref = terrain_surface
        self.before = None
        self.after = None

    def execute(self):
        manager = self.workspace.gis_manager.terrain_manager
        surface = manager.surface_for(self.surface_ref)
        if surface is None:
            return
        if self.before is None:
            self.before = deepcopy(surface.triangles)
        if self.after is None:
            manager.rebuild_surface(surface)
            self.after = deepcopy(surface.triangles)
        else:
            surface.triangles = deepcopy(self.after)

    def undo(self):
        surface = self.workspace.gis_manager.terrain_manager.surface_for(self.surface_ref)
        if surface is not None:
            surface.triangles = deepcopy(self.before or [])


class GenerateTerrainContoursCommand(Command):
    """Undoable command for terrain contour generation."""

    def __init__(self, workspace, terrain_surface, minor_interval=None, major_interval=None, smooth=False):
        self.workspace = workspace
        self.surface_ref = terrain_surface
        self.minor_interval = minor_interval
        self.major_interval = major_interval
        self.smooth = bool(smooth)
        self.before = None
        self.after = None

    def execute(self):
        manager = self.workspace.gis_manager.terrain_manager
        project = manager.ensure_project()
        if self.before is None:
            self.before = [contour.to_dict() for contour in project.contours]
        if self.after is None:
            manager.generate_contours(self.surface_ref, self.minor_interval, self.major_interval, self.smooth)
            self.after = [contour.to_dict() for contour in project.contours]
        else:
            from engine.terrain import TerrainContour
            project.contours = [TerrainContour.from_dict(item) for item in self.after]
            manager.refresh_diagnostics(project)

    def undo(self):
        from engine.terrain import TerrainContour
        manager = self.workspace.gis_manager.terrain_manager
        project = manager.ensure_project()
        project.contours = [TerrainContour.from_dict(item) for item in self.before or []]
        manager.refresh_diagnostics(project)


class ValidateTerrainProjectCommand(Command):
    """Undoable command for terrain validation."""

    def __init__(self, workspace):
        self.workspace = workspace
        self.before = None
        self.after = None

    def execute(self):
        manager = self.workspace.gis_manager.terrain_manager
        project = manager.ensure_project()
        if self.before is None:
            self.before = project.validation_report
        if self.after is None:
            self.after = manager.validate_project()
        else:
            project.validation_report = self.after
            manager.refresh_diagnostics(project)

    def undo(self):
        project = self.workspace.gis_manager.terrain_manager.ensure_project()
        project.validation_report = self.before
        self.workspace.gis_manager.terrain_manager.refresh_diagnostics(project)

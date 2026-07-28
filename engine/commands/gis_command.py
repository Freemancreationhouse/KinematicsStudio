from engine.commands.command import Command
from engine.gis import CRSDefinition, GISLayer, GISProject, SurveyPoint


class CreateGISProjectCommand(Command):
    """Undoable command for creating a GIS project inside the existing Workspace."""

    def __init__(self, workspace, name="GIS Project", default_crs="EPSG:4326", metadata=None):

        self.workspace = workspace
        self.project_name = name
        self.default_crs = default_crs
        self.metadata = dict(metadata or {})
        self.project = None

    def execute(self):
        """Create or restore the GIS project."""

        manager = self.workspace.gis_manager
        if self.project is None:
            self.project = manager.create_project(self.project_name, self.default_crs, self.metadata)
        else:
            manager.add_project(self.project)

    def undo(self):
        """Remove the GIS project."""

        if isinstance(self.project, GISProject) and self.project in self.workspace.gis_manager.projects:
            self.workspace.gis_manager.projects.remove(self.project)
            self.workspace.gis_manager.active_project_id = self.workspace.gis_manager.projects[-1].id if self.workspace.gis_manager.projects else None


class RegisterGISCRSCommand(Command):
    """Undoable command for adding CRS metadata to the GIS registry."""

    def __init__(self, workspace, definition):

        self.workspace = workspace
        self.definition = definition if isinstance(definition, CRSDefinition) else CRSDefinition.from_dict(definition)
        self.previous = None

    def execute(self):
        """Register CRS metadata."""

        registry = self.workspace.gis_manager.coordinate_systems.registry
        self.previous = registry.get(self.definition.code.upper())
        self.workspace.gis_manager.coordinate_systems.register_crs(self.definition)

    def undo(self):
        """Restore previous CRS registry state."""

        registry = self.workspace.gis_manager.coordinate_systems.registry
        if self.previous is None:
            registry.pop(self.definition.code.upper(), None)
        else:
            registry[self.previous.code.upper()] = self.previous


class AddGISLayerCommand(Command):
    """Undoable command for adding a GIS layer."""

    def __init__(self, workspace, layer):

        self.workspace = workspace
        self.layer = layer if isinstance(layer, GISLayer) else GISLayer.from_dict(layer)

    def execute(self):
        """Add the layer."""

        self.workspace.gis_manager.add_layer(self.layer)

    def undo(self):
        """Remove the layer."""

        self.workspace.gis_manager.remove_layer(self.layer)


class ImportGISFileCommand(Command):
    """Undoable command for importing a real GIS file."""

    def __init__(self, workspace, file_path, layer_name=None, target_crs=None, source_crs=None, import_as_survey=False):

        self.workspace = workspace
        self.file_path = file_path
        self.layer_name = layer_name
        self.target_crs = target_crs
        self.source_crs = source_crs
        self.import_as_survey = bool(import_as_survey)
        self.record = None
        self.layers = []
        self.survey_points = []

    def execute(self):
        """Import or restore GIS data."""

        project = self.workspace.gis_manager.ensure_project()
        if self.record is None:
            before_layers = set(layer.id for layer in project.layers)
            before_points = set(point.id for point in project.survey_points)
            self.record = self.workspace.gis_manager.import_file(
                self.file_path,
                self.layer_name,
                self.target_crs,
                self.source_crs,
                self.import_as_survey,
            )
            self.layers = [layer for layer in project.layers if layer.id not in before_layers]
            self.survey_points = [point for point in project.survey_points if point.id not in before_points]
        else:
            for layer in self.layers:
                self.workspace.gis_manager.add_layer(layer)
            for point in self.survey_points:
                if point not in project.survey_points:
                    project.survey_points.append(point)
            if self.record not in project.import_records:
                project.import_records.append(self.record)
            self.workspace.gis_manager.refresh_indexes(project)
            self.workspace.gis_manager.refresh_diagnostics(project)

    def undo(self):
        """Remove imported GIS data."""

        project = self.workspace.gis_manager.ensure_project()
        for layer in list(self.layers):
            self.workspace.gis_manager.remove_layer(layer)
        for point in list(self.survey_points):
            self.workspace.gis_manager.remove_survey_point(point)
        if self.record in project.import_records:
            project.import_records.remove(self.record)
        self.workspace.gis_manager.refresh_indexes(project)
        self.workspace.gis_manager.refresh_diagnostics(project)


class AddSurveyPointCommand(Command):
    """Undoable command for adding a survey, benchmark or control point."""

    def __init__(self, workspace, name, x, y, z=0.0, crs=None, point_type="Survey Point", elevation=None, metadata=None):

        self.workspace = workspace
        self.point_name = name
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.crs = crs
        self.point_type = point_type
        self.elevation = elevation
        self.metadata = dict(metadata or {})
        self.point = None

    def execute(self):
        """Create or restore survey point metadata."""

        project = self.workspace.gis_manager.ensure_project()
        if self.point is None:
            self.point = self.workspace.gis_manager.create_survey_point(
                self.point_name,
                self.x,
                self.y,
                self.z,
                self.crs,
                self.point_type,
                self.elevation,
                self.metadata,
            )
        elif self.point not in project.survey_points:
            project.survey_points.append(self.point)
            self.workspace.gis_manager.refresh_indexes(project)
            self.workspace.gis_manager.refresh_diagnostics(project)

    def undo(self):
        """Remove the survey point."""

        if isinstance(self.point, SurveyPoint):
            self.workspace.gis_manager.remove_survey_point(self.point)


class ValidateGISProjectCommand(Command):
    """Undoable command for refreshing GIS project validation."""

    def __init__(self, workspace):

        self.workspace = workspace
        self.before = None
        self.after = None

    def execute(self):
        """Run or restore GIS validation."""

        project = self.workspace.gis_manager.ensure_project()
        if self.before is None:
            self.before = project.validation_report
        if self.after is None:
            self.after = self.workspace.gis_manager.validate_project()
        else:
            project.validation_report = self.after
            self.workspace.gis_manager.refresh_diagnostics(project)

    def undo(self):
        """Restore previous GIS validation report."""

        project = self.workspace.gis_manager.ensure_project()
        project.validation_report = self.before
        self.workspace.gis_manager.refresh_diagnostics(project)


class RefreshGISIndexesCommand(Command):
    """Undoable command for rebuilding GIS project indexes."""

    def __init__(self, workspace):

        self.workspace = workspace
        self.before = None
        self.after = None

    def execute(self):
        """Build or restore GIS indexes."""

        project = self.workspace.gis_manager.ensure_project()
        if self.before is None:
            self.before = dict(project.indexes)
        if self.after is None:
            self.after = self.workspace.gis_manager.refresh_indexes(project)
        else:
            project.indexes = dict(self.after)

    def undo(self):
        """Restore previous GIS indexes."""

        self.workspace.gis_manager.ensure_project().indexes = dict(self.before or {})

from copy import deepcopy

from engine.commands.command import Command
from engine.infrastructure import InfrastructureProject


def _manager(workspace):
    return workspace.gis_manager.terrain_manager.site_engineering_manager.infrastructure_manager


class CreateInfrastructureProjectCommand(Command):
    """Undoable command for creating an infrastructure project."""

    def __init__(self, workspace, name="Infrastructure Project", settings=None, metadata=None):
        self.workspace = workspace
        self.project_name = name
        self.settings = settings
        self.metadata = dict(metadata or {})
        self.project = None

    def execute(self):
        manager = _manager(self.workspace)
        if self.project is None:
            self.project = manager.create_project(self.project_name, self.settings, self.metadata)
        elif self.project not in manager.projects:
            manager.projects.append(self.project)
            manager.active_project_id = self.project.id
            manager.refresh_diagnostics(self.project)

    def undo(self):
        manager = _manager(self.workspace)
        if isinstance(self.project, InfrastructureProject) and self.project in manager.projects:
            manager.projects.remove(self.project)
            manager.active_project_id = manager.projects[-1].id if manager.projects else None


class AddRoadCommand(Command):
    """Undoable command for road centerline and corridor metadata."""

    def __init__(self, workspace, name, centerline, horizontal_alignment=None, vertical_alignment=None, lanes=None, hierarchy="Local", metadata=None):
        self.workspace = workspace
        self.road_name = name
        self.centerline = [list(point) for point in centerline]
        self.horizontal_alignment = horizontal_alignment
        self.vertical_alignment = vertical_alignment
        self.lanes = [dict(item) for item in lanes or []]
        self.hierarchy = hierarchy
        self.metadata = dict(metadata or {})
        self.record = None

    def execute(self):
        manager = _manager(self.workspace)
        if self.record is None:
            self.record = manager.add_road(self.road_name, self.centerline, self.horizontal_alignment, self.vertical_alignment, self.lanes or None, self.hierarchy, self.metadata)
        else:
            project = manager.ensure_project()
            if self.record not in project.roads:
                project.roads.append(self.record)
            manager.rebuild_indexes(project)
            manager.refresh_diagnostics(project)

    def undo(self):
        manager = _manager(self.workspace)
        project = manager.ensure_project()
        project.roads = [item for item in project.roads if item.get("id") != self.record.get("id")]
        manager.rebuild_indexes(project)
        manager.refresh_diagnostics(project)


class EditRoadCommand(Command):
    """Undoable command for road editing."""

    def __init__(self, workspace, road_ref, **updates):
        self.workspace = workspace
        self.road_ref = road_ref
        self.updates = dict(updates)
        self.before = None
        self.after = None

    def execute(self):
        manager = _manager(self.workspace)
        road = manager.road_for(self.road_ref)
        if self.before is None:
            self.before = deepcopy(road)
        if self.after is None:
            manager.update_road(road, **self.updates)
            self.after = deepcopy(road)
        else:
            road.clear()
            road.update(deepcopy(self.after))
            manager.rebuild_indexes()
            manager.refresh_diagnostics()

    def undo(self):
        manager = _manager(self.workspace)
        road = manager.road_for(self.road_ref)
        road.clear()
        road.update(deepcopy(self.before))
        manager.rebuild_indexes()
        manager.refresh_diagnostics()


class AddParcelCommand(Command):
    """Undoable command for parcel/lots/blocks."""

    def __init__(self, workspace, name, boundary, attributes=None, ownership=None, subdivision=None):
        self.workspace = workspace
        self.parcel_name = name
        self.boundary = [list(point) for point in boundary]
        self.attributes = dict(attributes or {})
        self.ownership = dict(ownership or {})
        self.subdivision = dict(subdivision or {})
        self.record = None

    def execute(self):
        manager = _manager(self.workspace)
        if self.record is None:
            self.record = manager.add_parcel(self.parcel_name, self.boundary, self.attributes, self.ownership, self.subdivision)
        else:
            project = manager.ensure_project()
            if self.record not in project.parcels:
                project.parcels.append(self.record)
            manager.rebuild_indexes(project)
            manager.refresh_diagnostics(project)

    def undo(self):
        manager = _manager(self.workspace)
        project = manager.ensure_project()
        project.parcels = [item for item in project.parcels if item.get("id") != self.record.get("id")]
        manager.rebuild_indexes(project)
        manager.refresh_diagnostics(project)


class AddUtilityNetworkCommand(Command):
    """Undoable command for water, stormwater, sanitary, electrical, telecom and gas networks."""

    def __init__(self, workspace, network_type, name, nodes=None, edges=None, corridor=None, metadata=None):
        self.workspace = workspace
        self.network_type = network_type
        self.network_name = name
        self.nodes = [dict(item) for item in nodes or []]
        self.edges = [dict(item) for item in edges or []]
        self.corridor = dict(corridor or {})
        self.metadata = dict(metadata or {})
        self.record = None

    def execute(self):
        manager = _manager(self.workspace)
        if self.record is None:
            self.record = manager.add_utility_network(self.network_type, self.network_name, self.nodes, self.edges, self.corridor or None, self.metadata)
        else:
            project = manager.ensure_project()
            if self.record not in project.utility_networks:
                project.utility_networks.append(self.record)
            manager.rebuild_indexes(project)
            manager.refresh_diagnostics(project)

    def undo(self):
        manager = _manager(self.workspace)
        project = manager.ensure_project()
        project.utility_networks = [item for item in project.utility_networks if item.get("id") != self.record.get("id")]
        manager.rebuild_indexes(project)
        manager.refresh_diagnostics(project)


class AddSurveyAlignmentCommand(Command):
    """Undoable command for survey alignment objects."""

    def __init__(self, workspace, name, polyline, alignment_type="Survey Alignment", metadata=None):
        self.workspace = workspace
        self.alignment_name = name
        self.polyline = [list(point) for point in polyline]
        self.alignment_type = alignment_type
        self.metadata = dict(metadata or {})
        self.record = None

    def execute(self):
        manager = _manager(self.workspace)
        if self.record is None:
            self.record = manager.add_alignment(self.alignment_name, self.polyline, self.alignment_type, self.metadata)
        else:
            project = manager.ensure_project()
            if self.record not in project.alignments:
                project.alignments.append(self.record)
            manager.rebuild_indexes(project)
            manager.refresh_diagnostics(project)

    def undo(self):
        manager = _manager(self.workspace)
        project = manager.ensure_project()
        project.alignments = [item for item in project.alignments if item.get("id") != self.record.get("id")]
        manager.rebuild_indexes(project)
        manager.refresh_diagnostics(project)


class ImportOpenStreetMapCommand(Command):
    """Undoable command for real OpenStreetMap XML imports."""

    def __init__(self, workspace, file_path):
        self.workspace = workspace
        self.file_path = file_path
        self.snapshot = None
        self.record = None

    def execute(self):
        manager = _manager(self.workspace)
        project = manager.ensure_project()
        if self.snapshot is None:
            self.snapshot = _snapshot(project)
            self.record = manager.import_osm(self.file_path)
        else:
            _restore(project, self.snapshot)
            self.record = manager.import_osm(self.file_path)

    def undo(self):
        project = _manager(self.workspace).ensure_project()
        _restore(project, self.snapshot)
        _manager(self.workspace).refresh_diagnostics(project)


class ImportGeoPackageCommand(ImportOpenStreetMapCommand):
    """Undoable command for real GeoPackage imports."""

    def execute(self):
        manager = _manager(self.workspace)
        project = manager.ensure_project()
        if self.snapshot is None:
            self.snapshot = _snapshot(project)
        else:
            _restore(project, self.snapshot)
        self.record = manager.import_geopackage(self.file_path)


class SynchronizeInfrastructureGISCommand(ImportOpenStreetMapCommand):
    """Undoable command for GIS layer/file synchronization."""

    def __init__(self, workspace, file_path, layer_name=None):
        super().__init__(workspace, file_path)
        self.layer_name = layer_name

    def execute(self):
        manager = _manager(self.workspace)
        project = manager.ensure_project()
        if self.snapshot is None:
            self.snapshot = _snapshot(project)
        else:
            _restore(project, self.snapshot)
        self.record = manager.synchronize_file(self.file_path, self.layer_name)


class ValidateInfrastructureCommand(Command):
    """Undoable command for infrastructure validation."""

    def __init__(self, workspace):
        self.workspace = workspace
        self.before = None
        self.after = None

    def execute(self):
        manager = _manager(self.workspace)
        project = manager.ensure_project()
        if self.before is None:
            self.before = project.validation_report
        if self.after is None:
            self.after = manager.validate_project()
        else:
            project.validation_report = self.after
            manager.refresh_diagnostics(project)

    def undo(self):
        manager = _manager(self.workspace)
        project = manager.ensure_project()
        project.validation_report = self.before
        manager.refresh_diagnostics(project)


def _snapshot(project):
    return {
        "roads": deepcopy(project.roads),
        "parcels": deepcopy(project.parcels),
        "utility_networks": deepcopy(project.utility_networks),
        "alignments": deepcopy(project.alignments),
        "imports": deepcopy(project.imports),
        "synchronized_layers": deepcopy(project.synchronized_layers),
        "indexes": deepcopy(project.indexes),
    }


def _restore(project, snapshot):
    if not snapshot:
        return
    project.roads = deepcopy(snapshot["roads"])
    project.parcels = deepcopy(snapshot["parcels"])
    project.utility_networks = deepcopy(snapshot["utility_networks"])
    project.alignments = deepcopy(snapshot["alignments"])
    project.imports = deepcopy(snapshot["imports"])
    project.synchronized_layers = deepcopy(snapshot["synchronized_layers"])
    project.indexes = deepcopy(snapshot["indexes"])

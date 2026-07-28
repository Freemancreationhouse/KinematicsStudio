from copy import deepcopy

from engine.commands.command import Command
from engine.site_engineering import SiteProject


class CreateSiteEngineeringProjectCommand(Command):
    """Undoable command for creating a site engineering project."""

    def __init__(self, workspace, name="Site Engineering Project", settings=None, metadata=None):
        self.workspace = workspace
        self.project_name = name
        self.settings = settings
        self.metadata = dict(metadata or {})
        self.project = None

    def execute(self):
        manager = self.workspace.gis_manager.terrain_manager.site_engineering_manager
        if self.project is None:
            self.project = manager.create_project(self.project_name, self.settings, self.metadata)
        elif self.project not in manager.projects:
            manager.projects.append(self.project)
            manager.active_project_id = self.project.id
            manager.refresh_diagnostics(self.project)

    def undo(self):
        manager = self.workspace.gis_manager.terrain_manager.site_engineering_manager
        if isinstance(self.project, SiteProject) and self.project in manager.projects:
            manager.projects.remove(self.project)
            manager.active_project_id = manager.projects[-1].id if manager.projects else None


class AddSiteBoundaryCommand(Command):
    """Undoable command for property, construction and engineering constraint boundaries."""

    def __init__(self, workspace, name, boundary_type, polygon, metadata=None):
        self.workspace = workspace
        self.boundary_name = name
        self.boundary_type = boundary_type
        self.polygon = [list(point) for point in polygon]
        self.metadata = dict(metadata or {})
        self.record = None

    def execute(self):
        manager = self.workspace.gis_manager.terrain_manager.site_engineering_manager
        if self.record is None:
            self.record = manager.add_boundary(self.boundary_name, self.boundary_type, self.polygon, self.metadata)
        else:
            project = manager.ensure_project()
            if self.record not in project.boundaries:
                project.boundaries.append(self.record)
            manager.refresh_diagnostics(project)

    def undo(self):
        manager = self.workspace.gis_manager.terrain_manager.site_engineering_manager
        project = manager.ensure_project()
        project.boundaries = [item for item in project.boundaries if item.get("id") != self.record.get("id")]
        manager.refresh_diagnostics(project)


class ApplySiteGradingCommand(Command):
    """Undoable command for real terrain grading edits."""

    def __init__(self, workspace, terrain_surface, grading_type, region=None, parameters=None):
        self.workspace = workspace
        self.surface_ref = terrain_surface
        self.grading_type = grading_type
        self.region = dict(region or {})
        self.parameters = dict(parameters or {})
        self.before = None
        self.after = None
        self.record = None

    def execute(self):
        terrain = self.workspace.gis_manager.terrain_manager
        manager = terrain.site_engineering_manager
        surface = terrain.surface_for(self.surface_ref)
        if surface is None:
            return
        if self.before is None:
            self.before = deepcopy(surface.points)
        if self.after is None:
            self.record = manager.apply_grading(surface, self.grading_type, self.region, self.parameters)
            self.after = deepcopy(surface.points)
        else:
            surface.points = deepcopy(self.after)
            project = manager.ensure_project()
            if self.record and self.record not in project.grading_operations:
                project.grading_operations.append(self.record)
            terrain.refresh_diagnostics()
            manager.refresh_diagnostics(project)

    def undo(self):
        terrain = self.workspace.gis_manager.terrain_manager
        manager = terrain.site_engineering_manager
        surface = terrain.surface_for(self.surface_ref)
        if surface is not None:
            surface.points = deepcopy(self.before or [])
            terrain.refresh_diagnostics()
        project = manager.ensure_project()
        if self.record:
            project.grading_operations = [item for item in project.grading_operations if item.get("id") != self.record.get("id")]
        manager.refresh_diagnostics(project)


class ComputeCutFillCommand(Command):
    """Undoable command for earthwork volume reports."""

    def __init__(self, workspace, existing_surface, design_surface=None, region=None, name="Earthwork Volume"):
        self.workspace = workspace
        self.existing_surface = existing_surface
        self.design_surface = design_surface
        self.region = dict(region or {})
        self.report_name = name
        self.report = None

    def execute(self):
        manager = self.workspace.gis_manager.terrain_manager.site_engineering_manager
        if self.report is None:
            self.report = manager.compute_cut_fill(self.existing_surface, self.design_surface, self.region, self.report_name)
        else:
            project = manager.ensure_project()
            if self.report not in project.volume_reports:
                project.volume_reports.append(self.report)
            manager.refresh_diagnostics(project)

    def undo(self):
        manager = self.workspace.gis_manager.terrain_manager.site_engineering_manager
        project = manager.ensure_project()
        project.volume_reports = [item for item in project.volume_reports if item.get("id") != self.report.get("id")]
        manager.refresh_diagnostics(project)


class AnalyzeSiteSlopeCommand(Command):
    """Undoable command for site slope analysis reports."""

    def __init__(self, workspace, terrain_surface, region=None, classes=None, name="Slope Analysis"):
        self.workspace = workspace
        self.surface_ref = terrain_surface
        self.region = dict(region or {})
        self.classes = list(classes or [])
        self.report_name = name
        self.report = None

    def execute(self):
        manager = self.workspace.gis_manager.terrain_manager.site_engineering_manager
        if self.report is None:
            self.report = manager.analyze_slope(self.surface_ref, self.region, self.classes or None, self.report_name)
        else:
            project = manager.ensure_project()
            if self.report not in project.slope_reports:
                project.slope_reports.append(self.report)
            manager.refresh_diagnostics(project)

    def undo(self):
        manager = self.workspace.gis_manager.terrain_manager.site_engineering_manager
        project = manager.ensure_project()
        project.slope_reports = [item for item in project.slope_reports if item.get("id") != self.report.get("id")]
        manager.refresh_diagnostics(project)


class AnalyzeSiteDrainageCommand(Command):
    """Undoable command for drainage reports."""

    def __init__(self, workspace, terrain_surface, name="Drainage Analysis"):
        self.workspace = workspace
        self.surface_ref = terrain_surface
        self.report_name = name
        self.report = None

    def execute(self):
        manager = self.workspace.gis_manager.terrain_manager.site_engineering_manager
        if self.report is None:
            self.report = manager.analyze_drainage(self.surface_ref, self.report_name)
        else:
            project = manager.ensure_project()
            if self.report not in project.drainage_reports:
                project.drainage_reports.append(self.report)
            manager.refresh_diagnostics(project)

    def undo(self):
        manager = self.workspace.gis_manager.terrain_manager.site_engineering_manager
        project = manager.ensure_project()
        project.drainage_reports = [item for item in project.drainage_reports if item.get("id") != self.report.get("id")]
        manager.refresh_diagnostics(project)


class CreateSiteSectionCommand(Command):
    """Undoable command for cross-section generation."""

    def __init__(self, workspace, terrain_surface, name, line, interval=None, section_type="Cross Section"):
        self.workspace = workspace
        self.surface_ref = terrain_surface
        self.section_name = name
        self.line = [list(point) for point in line]
        self.interval = interval
        self.section_type = section_type
        self.record = None

    def execute(self):
        manager = self.workspace.gis_manager.terrain_manager.site_engineering_manager
        if self.record is None:
            self.record = manager.create_section(self.surface_ref, self.section_name, self.line, self.interval, self.section_type)
        else:
            project = manager.ensure_project()
            if self.record not in project.sections:
                project.sections.append(self.record)
            manager.refresh_diagnostics(project)

    def undo(self):
        manager = self.workspace.gis_manager.terrain_manager.site_engineering_manager
        project = manager.ensure_project()
        project.sections = [item for item in project.sections if item.get("id") != self.record.get("id")]
        manager.refresh_diagnostics(project)


class CreateSiteProfileCommand(Command):
    """Undoable command for longitudinal profile generation."""

    def __init__(self, workspace, terrain_surface, name, polyline, interval=None):
        self.workspace = workspace
        self.surface_ref = terrain_surface
        self.profile_name = name
        self.polyline = [list(point) for point in polyline]
        self.interval = interval
        self.record = None

    def execute(self):
        manager = self.workspace.gis_manager.terrain_manager.site_engineering_manager
        if self.record is None:
            self.record = manager.create_profile(self.surface_ref, self.profile_name, self.polyline, self.interval)
        else:
            project = manager.ensure_project()
            if self.record not in project.profiles:
                project.profiles.append(self.record)
            manager.refresh_diagnostics(project)

    def undo(self):
        manager = self.workspace.gis_manager.terrain_manager.site_engineering_manager
        project = manager.ensure_project()
        project.profiles = [item for item in project.profiles if item.get("id") != self.record.get("id")]
        manager.refresh_diagnostics(project)


class ValidateSiteEngineeringCommand(Command):
    """Undoable command for site engineering validation."""

    def __init__(self, workspace):
        self.workspace = workspace
        self.before = None
        self.after = None

    def execute(self):
        manager = self.workspace.gis_manager.terrain_manager.site_engineering_manager
        project = manager.ensure_project()
        if self.before is None:
            self.before = project.validation_report
        if self.after is None:
            self.after = manager.validate_project()
        else:
            project.validation_report = self.after
            manager.refresh_diagnostics(project)

    def undo(self):
        manager = self.workspace.gis_manager.terrain_manager.site_engineering_manager
        project = manager.ensure_project()
        project.validation_report = self.before
        manager.refresh_diagnostics(project)

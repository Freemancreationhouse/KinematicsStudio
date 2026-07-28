from copy import deepcopy

from engine.ai_site_intelligence import AISiteIntelligenceProject
from engine.commands.command import Command


def _manager(workspace):
    return workspace.gis_manager.terrain_manager.site_engineering_manager.infrastructure_manager.ai_site_intelligence_manager


class CreateAISiteIntelligenceProjectCommand(Command):
    """Undoable command for creating deterministic AI Site Intelligence metadata."""

    def __init__(self, workspace, name="AI Site Intelligence", settings=None, metadata=None):
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
        if isinstance(self.project, AISiteIntelligenceProject) and self.project in manager.projects:
            manager.projects.remove(self.project)
            manager.active_project_id = manager.projects[-1].id if manager.projects else None


class RunBuildabilityAnalysisCommand(Command):
    """Undoable command for deterministic buildability analysis."""

    def __init__(self, workspace, terrain_surface=None, name="Buildability Analysis"):
        self.workspace = workspace
        self.terrain_surface = terrain_surface
        self.report_name = name
        self.snapshot = None
        self.report = None

    def execute(self):
        manager = _manager(self.workspace)
        project = manager.ensure_project()
        if self.snapshot is None:
            self.snapshot = _snapshot(project)
        else:
            _restore(project, self.snapshot)
        self.report = manager.analyze_buildability(self.terrain_surface, self.report_name)

    def undo(self):
        project = _manager(self.workspace).ensure_project()
        _restore(project, self.snapshot)
        _manager(self.workspace).refresh_diagnostics(project)


class RunEnvironmentalAnalysisCommand(RunBuildabilityAnalysisCommand):
    """Undoable command for deterministic environmental analysis."""

    def execute(self):
        manager = _manager(self.workspace)
        project = manager.ensure_project()
        if self.snapshot is None:
            self.snapshot = _snapshot(project)
        else:
            _restore(project, self.snapshot)
        self.report = manager.analyze_environment(self.terrain_surface, self.report_name)


class RunSitePlanningCommand(RunBuildabilityAnalysisCommand):
    """Undoable command for deterministic site planning suggestions."""

    def execute(self):
        manager = _manager(self.workspace)
        project = manager.ensure_project()
        if self.snapshot is None:
            self.snapshot = _snapshot(project)
        else:
            _restore(project, self.snapshot)
        self.report = manager.plan_site(self.terrain_surface, self.report_name)


class RunConstraintIntelligenceCommand(RunBuildabilityAnalysisCommand):
    """Undoable command for deterministic constraint intelligence."""

    def execute(self):
        manager = _manager(self.workspace)
        project = manager.ensure_project()
        if self.snapshot is None:
            self.snapshot = _snapshot(project)
        else:
            _restore(project, self.snapshot)
        self.report = manager.detect_constraints(self.terrain_surface, self.report_name)


class GenerateAISiteEngineeringReportsCommand(Command):
    """Undoable command for AI Site Intelligence engineering reports."""

    def __init__(self, workspace, name="AI Site Intelligence Summary"):
        self.workspace = workspace
        self.report_name = name
        self.snapshot = None
        self.report = None

    def execute(self):
        manager = _manager(self.workspace)
        project = manager.ensure_project()
        if self.snapshot is None:
            self.snapshot = _snapshot(project)
        else:
            _restore(project, self.snapshot)
        self.report = manager.generate_reports(self.report_name)

    def undo(self):
        project = _manager(self.workspace).ensure_project()
        _restore(project, self.snapshot)
        _manager(self.workspace).refresh_diagnostics(project)


class ValidateAISiteIntelligenceCommand(Command):
    """Undoable command for AI Site Intelligence validation."""

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
        "buildability_reports": deepcopy(project.buildability_reports),
        "environmental_reports": deepcopy(project.environmental_reports),
        "planning_reports": deepcopy(project.planning_reports),
        "constraint_reports": deepcopy(project.constraint_reports),
        "engineering_reports": deepcopy(project.engineering_reports),
        "recommendations": deepcopy(project.recommendations),
        "validation_report": deepcopy(project.validation_report),
        "visualization_metadata": deepcopy(project.visualization_metadata),
    }


def _restore(project, snapshot):
    if not snapshot:
        return
    project.buildability_reports = deepcopy(snapshot["buildability_reports"])
    project.environmental_reports = deepcopy(snapshot["environmental_reports"])
    project.planning_reports = deepcopy(snapshot["planning_reports"])
    project.constraint_reports = deepcopy(snapshot["constraint_reports"])
    project.engineering_reports = deepcopy(snapshot["engineering_reports"])
    project.recommendations = deepcopy(snapshot["recommendations"])
    project.validation_report = deepcopy(snapshot["validation_report"])
    project.visualization_metadata = deepcopy(snapshot["visualization_metadata"])

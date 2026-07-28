from copy import deepcopy

from engine.commands.command import Command


def _runtime(workspace):
    return workspace.gis_manager.terrain_production_runtime


class InitializeTerrainProductionRuntimeCommand(Command):
    """Undoable command for production terrain runtime initialization metadata."""

    def __init__(self, workspace, configuration=None, recovery_metadata=None):
        self.workspace = workspace
        self.configuration = configuration
        self.recovery_metadata = dict(recovery_metadata or {})
        self.before = None
        self.session = None

    def execute(self):
        runtime = _runtime(self.workspace)
        if self.before is None:
            self.before = deepcopy(runtime.to_dict())
        self.session = runtime.initialize(self.configuration, self.recovery_metadata)

    def undo(self):
        _runtime(self.workspace).from_dict(self.before)


class OptimizeTerrainRuntimeCommand(Command):
    """Undoable command for production terrain runtime optimization."""

    def __init__(self, workspace):
        self.workspace = workspace
        self.before = None
        self.report = None

    def execute(self):
        runtime = _runtime(self.workspace)
        if self.before is None:
            self.before = deepcopy(runtime.to_dict())
        self.report = runtime.optimize_project()

    def undo(self):
        _runtime(self.workspace).from_dict(self.before)


class ValidateTerrainRuntimeCommand(Command):
    """Undoable command for production terrain runtime validation."""

    def __init__(self, workspace):
        self.workspace = workspace
        self.before = None
        self.report = None

    def execute(self):
        runtime = _runtime(self.workspace)
        if self.before is None:
            self.before = deepcopy(runtime.to_dict())
        self.report = runtime.validate_runtime(self.workspace)

    def undo(self):
        _runtime(self.workspace).from_dict(self.before)


class RunTerrainProductionRegressionCommand(Command):
    """Undoable command for production terrain regression metadata."""

    def __init__(self, workspace):
        self.workspace = workspace
        self.before = None
        self.result = None

    def execute(self):
        runtime = _runtime(self.workspace)
        if self.before is None:
            self.before = deepcopy(runtime.to_dict())
        self.result = runtime.run_regression_suite()

    def undo(self):
        _runtime(self.workspace).from_dict(self.before)


class CertifyTerrainCompatibilityCommand(Command):
    """Undoable command for production terrain compatibility certification."""

    def __init__(self, workspace):
        self.workspace = workspace
        self.before = None
        self.report = None

    def execute(self):
        runtime = _runtime(self.workspace)
        if self.before is None:
            self.before = deepcopy(runtime.to_dict())
        self.report = runtime.certify_compatibility()

    def undo(self):
        _runtime(self.workspace).from_dict(self.before)


class CertifyTerrainReleaseCommand(Command):
    """Undoable command for Release 2.0 production certification."""

    def __init__(self, workspace):
        self.workspace = workspace
        self.before = None
        self.record = None

    def execute(self):
        runtime = _runtime(self.workspace)
        if self.before is None:
            self.before = deepcopy(runtime.to_dict())
        self.record = runtime.certify_release(self.workspace)

    def undo(self):
        _runtime(self.workspace).from_dict(self.before)


class CleanupTerrainRuntimeCommand(Command):
    """Undoable command for runtime cleanup metadata."""

    def __init__(self, workspace):
        self.workspace = workspace
        self.before = None
        self.event = None

    def execute(self):
        runtime = _runtime(self.workspace)
        if self.before is None:
            self.before = deepcopy(runtime.to_dict())
        self.event = runtime.cleanup_resources()

    def undo(self):
        _runtime(self.workspace).from_dict(self.before)


class GenerateTerrainRuntimeVisualizationCommand(Command):
    """Undoable command for renderer-consumable runtime visualization metadata."""

    def __init__(self, workspace):
        self.workspace = workspace
        self.before = None
        self.metadata = None

    def execute(self):
        runtime = _runtime(self.workspace)
        if self.before is None:
            self.before = deepcopy(runtime.to_dict())
        self.metadata = runtime.visualization_metadata()

    def undo(self):
        _runtime(self.workspace).from_dict(self.before)

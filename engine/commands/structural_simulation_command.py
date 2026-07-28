"""Undoable commands for structural simulation execution."""

from engine.commands.command import Command
from engine.simulation.workspace import SIMULATION_WORKSPACE_SETTINGS_KEY


class RunStructuralStudyCommand(Command):
    """Execute a structural study through the existing Simulation Workspace."""

    def __init__(self, workspace, study):

        self.workspace = workspace
        self.study = study
        self.before = None
        self.after = None

    def execute(self):
        """Run the structural solver and store results through SimulationWorkspace."""

        simulation = self.workspace.simulation_workspace
        if self.after is not None:
            self._restore(self.after)
            return
        self.before = simulation.to_dict()
        simulation.execute_structural_study(self.study)
        self.after = simulation.to_dict()

    def undo(self):
        """Restore simulation state from before structural execution."""

        if self.before is not None:
            self._restore(self.before)

    def _restore(self, state):
        simulation = self.workspace.simulation_workspace
        simulation.workspace.project_settings[SIMULATION_WORKSPACE_SETTINGS_KEY] = state
        simulation.load_from_settings()


class RunBuildingStructuralStudyCommand(RunStructuralStudyCommand):
    """Execute a building structural study through the existing structural solver."""

    def execute(self):
        """Run building structural analysis and store results through SimulationWorkspace."""

        simulation = self.workspace.simulation_workspace
        if self.after is not None:
            self._restore(self.after)
            return
        self.before = simulation.to_dict()
        simulation.execute_building_structural_study(self.study)
        self.after = simulation.to_dict()


class RunThermalStudyCommand(RunStructuralStudyCommand):
    """Execute a thermal study through the existing simulation workspace."""

    def execute(self):
        """Run thermal analysis and store results through SimulationWorkspace."""

        simulation = self.workspace.simulation_workspace
        if self.after is not None:
            self._restore(self.after)
            return
        self.before = simulation.to_dict()
        simulation.execute_thermal_study(self.study)
        self.after = simulation.to_dict()


class RunDaylightStudyCommand(RunStructuralStudyCommand):
    """Execute a daylight study through the existing simulation workspace."""

    def execute(self):
        """Run daylight analysis and store results through SimulationWorkspace."""

        simulation = self.workspace.simulation_workspace
        if self.after is not None:
            self._restore(self.after)
            return
        self.before = simulation.to_dict()
        simulation.execute_daylight_study(self.study)
        self.after = simulation.to_dict()


class RunEnergyStudyCommand(RunStructuralStudyCommand):
    """Execute an energy study through the existing simulation workspace."""

    def execute(self):
        """Run energy analysis and store results through SimulationWorkspace."""

        simulation = self.workspace.simulation_workspace
        if self.after is not None:
            self._restore(self.after)
            return
        self.before = simulation.to_dict()
        simulation.execute_energy_study(self.study)
        self.after = simulation.to_dict()


class RunCFDStudyCommand(RunStructuralStudyCommand):
    """Execute a CFD study through the existing simulation workspace."""

    def execute(self):
        """Run CFD analysis and store results through SimulationWorkspace."""

        simulation = self.workspace.simulation_workspace
        if self.after is not None:
            self._restore(self.after)
            return
        self.before = simulation.to_dict()
        simulation.execute_cfd_study(self.study)
        self.after = simulation.to_dict()


class RunMotionStudyCommand(RunStructuralStudyCommand):
    """Execute a motion study through the existing simulation workspace."""

    def execute(self):
        """Run motion analysis and store results through SimulationWorkspace."""

        simulation = self.workspace.simulation_workspace
        if self.after is not None:
            self._restore(self.after)
            return
        self.before = simulation.to_dict()
        simulation.execute_motion_study(self.study)
        self.after = simulation.to_dict()


class RunOptimizationStudyCommand(RunStructuralStudyCommand):
    """Execute an optimization study through the existing simulation workspace."""

    def execute(self):
        """Run engineering optimization and store results through SimulationWorkspace."""

        simulation = self.workspace.simulation_workspace
        if self.after is not None:
            self._restore(self.after)
            return
        self.before = simulation.to_dict()
        simulation.execute_optimization_study(self.study)
        self.after = simulation.to_dict()

from copy import deepcopy
from pathlib import Path

from engine.commands.command import Command


class MachineCAMCommand(Command):
    """Base command for Machine/CAM actions routed through CommandManager."""

    def __init__(self, workspace):
        self.workspace = workspace
        self._before = None

    @property
    def machine_workspace(self):
        """Return the existing Workspace-owned Machine Workspace."""

        return self.workspace.machine_workspace

    @property
    def manufacturing_engine(self):
        """Return the existing Workspace-owned Manufacturing Engine."""

        return self.workspace.manufacturing_engine

    def execute(self):
        """Snapshot manufacturing metadata and execute the concrete action."""

        if self._before is None:
            self._before = self._state()
        self._execute()

    def undo(self):
        """Restore Machine/CAM metadata without modifying geometry."""

        if self._before is not None:
            self._restore(self._before)

    def _execute(self):
        raise NotImplementedError

    def _state(self):
        return {
            "project_settings": deepcopy(getattr(self.workspace, "project_settings", {})),
            "product_manager": deepcopy(self.workspace.product_manager.to_dict()),
        }

    def _restore(self, state):
        self.workspace.project_settings = deepcopy(state["project_settings"])
        self.workspace.product_manager.clear()
        self.workspace.product_manager.from_dict(deepcopy(state["product_manager"]))
        self.machine_workspace.load_from_settings()
        self.manufacturing_engine.load_from_settings()

    def _ensure_initialized(self):
        self.machine_workspace.initialize()
        self.machine_workspace.activate("Machine Workspace")
        self.manufacturing_engine.initialize()

    def _active_job(self):
        engine = self.manufacturing_engine
        if engine.state.active_job_id:
            job = engine.job_for(engine.state.active_job_id)
            if job is not None:
                return job
        if self.workspace.product_manager.cam_jobs:
            return self.workspace.product_manager.cam_jobs[-1]
        return None

    def _ensure_machine_profile(self):
        self._ensure_initialized()
        manager = self.workspace.product_manager.machine_library_manager
        if self.machine_workspace.state.active_profile_id:
            profile = manager.profile_for(self.machine_workspace.state.active_profile_id)
            if profile is not None:
                return profile
        if self.workspace.product_manager.machine_profiles:
            profile = self.workspace.product_manager.machine_profiles[-1]
            self.machine_workspace.activate_profile(profile)
            return profile
        profile_command = CreateMachineProfileCommand(self.workspace)
        profile_command._execute()
        return profile_command.profile

    def _ensure_job(self):
        job = self._active_job()
        if job is not None:
            return job
        command = CreateManufacturingJobCommand(self.workspace)
        command._execute()
        return command.job

    def _ensure_operation(self, job):
        operations = self.manufacturing_engine.operations_for_job(job)
        if operations:
            return operations[0]
        tool = self.workspace.product_manager.tool_definitions[0] if self.workspace.product_manager.tool_definitions else None
        return self.manufacturing_engine.create_operation(
            job,
            "2D Profile",
            name=f"{job.name} Profile Operation",
            required_tool=tool,
            depth=3.0,
            stepover=1.0,
            stepdown=0.5,
            cut_geometry={
                "estimated_path_length": 240.0,
                "bounds": {"x": 120.0, "y": 80.0, "z": 3.0},
            },
            metadata={
                "source": "Machine/CAM Workspace",
                "command_routed": True,
            },
        )

    def _ensure_toolpaths(self, job):
        self._ensure_operation(job)
        return self.manufacturing_engine.generate_toolpaths(job)

    def _ensure_program(self, job, controller="Generic ISO G-code"):
        self._ensure_toolpaths(job)
        return self.manufacturing_engine.generate_gcode(job, controller=controller)

    def _ensure_connection(self, profile=None):
        profile = profile or self._ensure_machine_profile()
        for connection in self.manufacturing_engine.machine_connections:
            if connection.machine_profile_id == profile.id:
                if connection.state != "Connected":
                    self.manufacturing_engine.connect_machine(connection)
                return connection
        connection = self.manufacturing_engine.create_machine_connection(
            profile,
            protocol="GRBL",
            connection_type="Serial",
            parameters={
                "port": "metadata://machine-workspace",
                "baud": 115200,
                "virtual_dispatch": True,
            },
        )
        return self.manufacturing_engine.connect_machine(connection)

    def _latest_session(self):
        sessions = self.manufacturing_engine.communication_sessions
        return sessions[-1] if sessions else None


class InitializeMachineCAMWorkspaceCommand(MachineCAMCommand):
    """Initialize the Machine Workspace and Manufacturing Engine."""

    def _execute(self):
        self._ensure_initialized()


class CreateMachineProfileCommand(MachineCAMCommand):
    """Create and activate a production machine profile."""

    def __init__(self, workspace, name="KS CNC Mill Profile"):
        super().__init__(workspace)
        self.profile_name = name
        self.machine = None
        self.profile = None

    def _execute(self):
        self._ensure_initialized()
        product = self.workspace.product_manager
        existing = product.machine_library_manager.profile_for(self.profile_name)
        if existing is not None:
            self.profile = self.machine_workspace.activate_profile(existing)
            return
        machine_name = f"{self.profile_name} Machine"
        self.machine = product.machine_library_manager.machine_for(machine_name)
        if self.machine is None:
            self.machine = self.machine_workspace.register_machine(
                machine_name,
                "CNC Mill",
                manufacturer="Kinematics Studio",
                model="Production CAM Reference",
                firmware="GRBL-compatible",
                work_envelope={"x": 500.0, "y": 400.0, "z": 150.0},
                supported_materials=["Aluminum", "Hardwood", "Engineering Plastic"],
                supported_tool_systems=["ER11", "ER16"],
                supported_file_formats=["gcode", "nc", "tap"],
            )
        tool_library = self.machine_workspace.create_tool_library("KS CAM Tool Library")
        if not product.tool_definitions:
            self.machine_workspace.register_tool(
                tool_library,
                "6 mm Flat End Mill",
                "Flat End Mill",
                diameter=6.0,
                length=50.0,
                material="Carbide",
                operating_limits={"flutes": 2, "max_rpm": 24000.0},
            )
        if not product.engineering_materials:
            self.machine_workspace.register_material(
                "6061 Aluminum",
                "Metal",
                density=2.7,
                manufacturing_notes="Good machinability; mist coolant recommended.",
                default_process_metadata={"yield_strength_mpa": 276.0, "coolant": "Mist"},
            )
        self.profile = self.machine_workspace.create_profile(
            self.machine,
            self.profile_name,
            tool_library=tool_library,
            metadata=None,
        )
        self.machine_workspace.activate_profile(self.profile)


class CreateManufacturingJobCommand(MachineCAMCommand):
    """Create a CAM job with setup metadata and one command-routed operation."""

    def __init__(self, workspace, name="KS Production CAM Job"):
        super().__init__(workspace)
        self.job_name = name
        self.job = None

    def _execute(self):
        profile = self._ensure_machine_profile()
        product = self.workspace.product_manager
        material = product.engineering_materials[0] if product.engineering_materials else None
        existing = next((job for job in product.cam_jobs if job.name == self.job_name), None)
        if existing is not None:
            self.job = self.manufacturing_engine.activate_job(existing)
            return
        self.job = self.manufacturing_engine.create_job(
            self.job_name,
            description="Command-routed Machine/CAM workspace production job.",
            machine_profile=profile,
            material=material,
            status="Pending",
            targets=[],
        )
        self.manufacturing_engine.create_stock(
            self.job,
            stock_type="Box",
            dimensions={"x": 120.0, "y": 80.0, "z": 12.0},
            material=material,
            allowance=1.0,
            notes="Production CAM validation stock.",
        )
        self.manufacturing_engine.create_coordinate_system(
            self.job,
            "G54 Work Coordinate System",
            activate=True,
        )
        self.manufacturing_engine.create_work_offset(
            self.job,
            "G54",
            translation={"x": 0.0, "y": 0.0, "z": 0.0},
        )
        self._ensure_operation(self.job)
        self.manufacturing_engine.transition_job(self.job, "Ready")


class GenerateToolpathCommand(MachineCAMCommand):
    """Generate validated toolpaths for the active manufacturing job."""

    def __init__(self, workspace, job=None):
        super().__init__(workspace)
        self.job = job
        self.toolpaths = []

    def _execute(self):
        job = self.manufacturing_engine.job_for(self.job) if self.job is not None else self._ensure_job()
        self.toolpaths = self._ensure_toolpaths(job)


class SimulateManufacturingJobCommand(MachineCAMCommand):
    """Run virtual manufacturing simulation for the active job."""

    def __init__(self, workspace, job=None):
        super().__init__(workspace)
        self.job = job
        self.simulation = None
        self.session = None
        self.collision_report = None
        self.verification = None
        self.report = None

    def _execute(self):
        job = self.manufacturing_engine.job_for(self.job) if self.job is not None else self._ensure_job()
        self._ensure_toolpaths(job)
        self._ensure_program(job)
        self.simulation = self.manufacturing_engine.create_simulation_job(job, process_type="CNC")
        self.session = self.manufacturing_engine.run_simulation(self.simulation)
        self.collision_report = self.manufacturing_engine.check_simulation_collisions(self.simulation)
        self.verification = self.manufacturing_engine.verify_simulation(self.simulation)
        self.report = self.manufacturing_engine.generate_simulation_report(self.simulation)


class PostProcessManufacturingJobCommand(MachineCAMCommand):
    """Generate reusable controller-specific G-code for the active job."""

    SUPPORTED_POSTS = {
        "Generic G-code": "Generic ISO G-code",
        "Generic ISO G-code": "Generic ISO G-code",
        "GRBL": "GRBL",
        "Marlin": "Marlin",
        "Klipper": "Klipper",
        "FluidNC": "FluidNC",
        "LinuxCNC": "LinuxCNC",
    }

    def __init__(self, workspace, job=None, controller="Generic G-code"):
        super().__init__(workspace)
        self.job = job
        self.controller = controller
        self.program = None

    def _execute(self):
        job = self.manufacturing_engine.job_for(self.job) if self.job is not None else self._ensure_job()
        controller = self.SUPPORTED_POSTS.get(self.controller, self.controller)
        self.program = self._ensure_program(job, controller)


class ExportManufacturingJobCommand(MachineCAMCommand):
    """Export the active job's generated program to a G-code file."""

    def __init__(self, workspace, output_path=None, job=None, controller="Generic G-code"):
        super().__init__(workspace)
        self.output_path = Path(output_path) if output_path else None
        self.job = job
        self.controller = controller
        self.program = None
        self.export_path = None

    def _execute(self):
        post = PostProcessManufacturingJobCommand(self.workspace, self.job, self.controller)
        post._execute()
        self.program = post.program
        target = self.output_path or Path(".tmp_test_output/release_3_batch_e/exports") / f"{self.program.program_name.lower()}.gcode"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.program.gcode, encoding="utf-8")
        self.export_path = target
        self.workspace.project_settings.setdefault("machine_cam_exports", {})["latest"] = {
            "path": str(target),
            "program_id": self.program.id,
            "controller": self.program.controller,
            "lines": self.program.statistics.get("lines", 0),
        }


class QueueManufacturingJobCommand(MachineCAMCommand):
    """Queue and upload the active manufacturing job through existing machine dispatch metadata."""

    def __init__(self, workspace, job=None, priority=0):
        super().__init__(workspace)
        self.job = job
        self.priority = priority
        self.connection = None
        self.queue_item = None
        self.session = None

    def _execute(self):
        job = self.manufacturing_engine.job_for(self.job) if self.job is not None else self._ensure_job()
        profile = self._ensure_machine_profile()
        self._ensure_program(job)
        self.connection = self._ensure_connection(profile)
        self.queue_item = self.manufacturing_engine.queue_machine_job(
            job,
            self.connection,
            priority=self.priority,
            source="Machine/CAM Workspace",
        )
        self.session = self.manufacturing_engine.upload_machine_job(self.queue_item)


class ExecuteManufacturingJobCommand(MachineCAMCommand):
    """Start an uploaded manufacturing communication session."""

    def __init__(self, workspace, session=None):
        super().__init__(workspace)
        self.session = session
        self.running_session = None

    def _execute(self):
        session = self.session or self._latest_session()
        if session is None:
            queue = QueueManufacturingJobCommand(self.workspace)
            queue._execute()
            session = queue.session
        self.running_session = self.manufacturing_engine.start_machine_job(session)


class PauseManufacturingJobCommand(MachineCAMCommand):
    """Pause the active manufacturing communication session."""

    def __init__(self, workspace, session=None):
        super().__init__(workspace)
        self.session = session
        self.paused_session = None

    def _execute(self):
        session = self.session or self._latest_session()
        if session is None:
            raise ValueError("Pause requires an uploaded or running manufacturing session.")
        self.paused_session = self.manufacturing_engine.pause_machine_job(session)


class ResumeManufacturingJobCommand(PauseManufacturingJobCommand):
    """Resume the active paused manufacturing communication session."""

    def _execute(self):
        session = self.session or self._latest_session()
        if session is None:
            raise ValueError("Resume requires a paused manufacturing session.")
        self.paused_session = self.manufacturing_engine.resume_machine_job(session)


class CancelManufacturingJobCommand(PauseManufacturingJobCommand):
    """Cancel/stop the active manufacturing communication session."""

    def _execute(self):
        session = self.session or self._latest_session()
        if session is None:
            raise ValueError("Cancel requires an uploaded or running manufacturing session.")
        self.paused_session = self.manufacturing_engine.stop_machine_job(session)


class CaptureMachineDiagnosticsCommand(MachineCAMCommand):
    """Capture Machine Workspace and Manufacturing Engine diagnostics."""

    def __init__(self, workspace):
        super().__init__(workspace)
        self.machine_report = None
        self.engine_report = None
        self.diagnostics = None

    def _execute(self):
        self._ensure_initialized()
        validation = self.machine_workspace.validate()
        engine_validation = self.manufacturing_engine.validate()
        self.machine_report = self.machine_workspace.diagnostics()
        self.engine_report = self.manufacturing_engine.diagnostics()
        self.diagnostics = {
            "machine_workspace": self.machine_report.to_dict(),
            "manufacturing_engine": self.engine_report.to_dict(),
            "validation": validation.to_dict(),
            "engine_validation": engine_validation.to_dict(),
        }
        self.workspace.project_settings["machine_cam_diagnostics"] = deepcopy(self.diagnostics)

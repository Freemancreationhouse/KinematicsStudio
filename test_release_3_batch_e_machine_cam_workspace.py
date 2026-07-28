import os
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from engine.commands import (
    CancelManufacturingJobCommand,
    CaptureMachineDiagnosticsCommand,
    CreateMachineProfileCommand,
    CreateManufacturingJobCommand,
    ExecuteManufacturingJobCommand,
    ExportManufacturingJobCommand,
    GenerateToolpathCommand,
    PauseManufacturingJobCommand,
    PostProcessManufacturingJobCommand,
    QueueManufacturingJobCommand,
    ResumeManufacturingJobCommand,
    SimulateManufacturingJobCommand,
)
from engine.storage import ProjectSerializer
from ui_v2.main_window import MainWindow


REQUIRED_MACHINE_BUTTONS = {
    "Machine::Machine Profile",
    "Machine::Create Job",
    "Machine::Generate Toolpath",
    "Machine::Simulate",
    "Machine::Post Process",
    "Machine::Export",
    "Machine::Queue Job",
    "Machine::Execute Job",
    "Machine::Pause",
    "Machine::Resume",
    "Machine::Cancel Job",
    "Machine::Diagnostics",
}


LAST_PERFORMANCE_SUMMARY = {}


def _visible_buttons(window):
    names = set()
    for index in range(window.ribbon.tabs.count()):
        tab = window.ribbon.tabs.widget(index)
        tab_name = window.ribbon.tabs.tabText(index)
        for button in tab.findChildren(QPushButton):
            if button.isVisibleTo(tab):
                names.add(f"{tab_name}::{button.text()}")
    return names


def test_release_3_batch_e_machine_cam_workspace(tmp_path):
    app = QApplication.instance() or QApplication([])
    start = time.perf_counter()
    window = MainWindow()
    startup_seconds = time.perf_counter() - start

    try:
        assert "Machine" in [
            window.ribbon.tabs.tabText(index)
            for index in range(window.ribbon.tabs.count())
        ]
        visible = _visible_buttons(window)
        assert REQUIRED_MACHINE_BUTTONS <= visible
        assert "Machine::Connect" not in visible
        assert "Machine::Jog" not in visible
        assert window.ribbon.hidden_tabs == {}

        workspace = window.canvas.app.workspace
        manager = workspace.command_manager

        profile_start = time.perf_counter()
        profile_command = CreateMachineProfileCommand(workspace)
        manager.execute(profile_command)
        profile_seconds = time.perf_counter() - profile_start
        assert profile_command.profile is not None
        assert workspace.machine_workspace.state.active is True
        assert workspace.machine_workspace.state.active_profile_id == profile_command.profile.id

        job_start = time.perf_counter()
        job_command = CreateManufacturingJobCommand(workspace)
        manager.execute(job_command)
        job_seconds = time.perf_counter() - job_start
        assert job_command.job is not None
        assert workspace.manufacturing_engine.state.active_job_id == job_command.job.id
        assert workspace.manufacturing_engine.operations_for_job(job_command.job)

        toolpath_start = time.perf_counter()
        toolpath_command = GenerateToolpathCommand(workspace, job_command.job)
        manager.execute(toolpath_command)
        toolpath_seconds = time.perf_counter() - toolpath_start
        assert toolpath_command.toolpaths
        assert all(path.valid for path in toolpath_command.toolpaths)

        simulation_start = time.perf_counter()
        simulation_command = SimulateManufacturingJobCommand(workspace, job_command.job)
        manager.execute(simulation_command)
        simulation_seconds = time.perf_counter() - simulation_start
        assert simulation_command.session.status == "Completed"
        assert simulation_command.report.valid

        post_start = time.perf_counter()
        generated_posts = []
        for controller in ("Generic G-code", "GRBL", "Marlin", "Klipper", "FluidNC", "LinuxCNC"):
            post_command = PostProcessManufacturingJobCommand(workspace, job_command.job, controller)
            manager.execute(post_command)
            assert post_command.program.valid
            assert "G21" in post_command.program.gcode
            generated_posts.append(post_command.program.controller)
        post_seconds = time.perf_counter() - post_start
        assert {"Generic ISO G-code", "GRBL", "Marlin", "Klipper", "FluidNC", "LinuxCNC"} <= set(generated_posts)

        export_start = time.perf_counter()
        export_path = Path(tmp_path) / "batch_e_cam_job.gcode"
        export_command = ExportManufacturingJobCommand(workspace, export_path, job_command.job, "GRBL")
        manager.execute(export_command)
        export_seconds = time.perf_counter() - export_start
        assert export_path.exists()
        assert "G21" in export_path.read_text(encoding="utf-8")

        queue_start = time.perf_counter()
        queue_command = QueueManufacturingJobCommand(workspace, job_command.job, priority=5)
        manager.execute(queue_command)
        execute_command = ExecuteManufacturingJobCommand(workspace, queue_command.session)
        manager.execute(execute_command)
        pause_command = PauseManufacturingJobCommand(workspace, execute_command.running_session)
        manager.execute(pause_command)
        resume_command = ResumeManufacturingJobCommand(workspace, pause_command.paused_session)
        manager.execute(resume_command)
        cancel_command = CancelManufacturingJobCommand(workspace, resume_command.paused_session)
        manager.execute(cancel_command)
        queue_seconds = time.perf_counter() - queue_start
        assert queue_command.queue_item.status == "Stopped"
        assert cancel_command.paused_session.state == "Stopped"

        diagnostics_command = CaptureMachineDiagnosticsCommand(workspace)
        manager.execute(diagnostics_command)
        assert diagnostics_command.diagnostics["validation"]["valid"] is True
        assert diagnostics_command.diagnostics["engine_validation"]["valid"] is True

        undo_count = manager.undo_count
        manager.undo()
        assert manager.redo_count == 1
        manager.redo()
        assert manager.undo_count == undo_count

        save_start = time.perf_counter()
        project_path = Path(tmp_path) / "release_3_batch_e_machine_cam.ksproj"
        ProjectSerializer().save(workspace, project_path)
        save_seconds = time.perf_counter() - save_start

        load_start = time.perf_counter()
        restored = ProjectSerializer().load(project_path)
        load_seconds = time.perf_counter() - load_start
        assert restored.machine_workspace.state.active is True
        assert restored.product_manager.machine_profiles
        assert restored.product_manager.cam_jobs
        assert restored.manufacturing_engine.toolpaths
        assert restored.manufacturing_engine.generated_programs
        assert restored.manufacturing_engine.communication_queue
        assert restored.manufacturing_engine.communication_sessions

        window.canvas.update()
        window.viewport3d.update()
        app.processEvents()

        global LAST_PERFORMANCE_SUMMARY
        LAST_PERFORMANCE_SUMMARY = {
            "startup_seconds": startup_seconds,
            "profile_seconds": profile_seconds,
            "job_seconds": job_seconds,
            "toolpath_seconds": toolpath_seconds,
            "simulation_seconds": simulation_seconds,
            "post_seconds": post_seconds,
            "export_seconds": export_seconds,
            "queue_seconds": queue_seconds,
            "save_seconds": save_seconds,
            "load_seconds": load_seconds,
        }
        assert startup_seconds < 5.0, LAST_PERFORMANCE_SUMMARY
        assert profile_seconds < 1.0, LAST_PERFORMANCE_SUMMARY
        assert job_seconds < 1.0, LAST_PERFORMANCE_SUMMARY
        assert toolpath_seconds < 1.0, LAST_PERFORMANCE_SUMMARY
        assert simulation_seconds < 1.0, LAST_PERFORMANCE_SUMMARY
        assert post_seconds < 1.0, LAST_PERFORMANCE_SUMMARY
        assert export_seconds < 1.0, LAST_PERFORMANCE_SUMMARY
        assert queue_seconds < 1.0, LAST_PERFORMANCE_SUMMARY
        assert save_seconds < 2.0, LAST_PERFORMANCE_SUMMARY
        assert load_seconds < 2.0, LAST_PERFORMANCE_SUMMARY

    finally:
        window.close()


if __name__ == "__main__":
    output = Path(".tmp_test_output/release_3_batch_e")
    output.mkdir(parents=True, exist_ok=True)
    test_release_3_batch_e_machine_cam_workspace(output)
    timings = " ".join(
        f"{key}={value:.4f}"
        for key, value in sorted(LAST_PERFORMANCE_SUMMARY.items())
    )
    print(f"release-3-batch-e-machine-cam-ok {timings}")

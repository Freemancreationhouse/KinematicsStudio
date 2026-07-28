import os
import py_compile
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.commands import AddEntityCommand
from engine.entities import LineEntity
from engine.capability_matrix import release_3_master_capability_matrix
from engine.geometry import Vector2
from engine.repository_certification import certify_repository
from engine.storage import ProjectSerializer
from engine.workspace.workspace import Workspace
from ui_v2.main_window import MainWindow


VALID_SOURCE_CLASSIFICATIONS = {
    "PRODUCTION",
    "SHARED",
    "INTERNAL",
    "LEGACY",
    "EXPERIMENTAL",
    "TEST",
    "DEPRECATED",
    "UNUSED",
}


LAST_PERFORMANCE_SUMMARY = {}


def test_release_3_batch_g_repository_certification(tmp_path):
    start = time.perf_counter()
    report = certify_repository()
    audit_seconds = time.perf_counter() - start

    assert len(report.source_files) >= 900
    assert all(record.classification in VALID_SOURCE_CLASSIFICATIONS for record in report.source_files)
    assert all(record.purpose for record in report.source_files)
    assert all(record.owner for record in report.source_files)
    assert all(record.runtime_usage for record in report.source_files)
    assert all(record.production_status for record in report.source_files)

    assert report.dependency_summary["python_files"] >= 900
    assert report.dependency_summary["broken_local_imports"] == []
    assert report.dependency_summary["circular_imports_detected"] == 0
    assert report.command_summary["command_classes"] >= 400
    assert report.command_summary["all_command_classes_certified"] is True
    assert report.ui_summary["production_ui_files"] >= 30
    assert report.ui_summary["legacy_ui_files_verified"] >= 1
    assert report.workspace_summary["single_workspace_owner"] is True
    assert report.capability_summary["capabilities"] >= 47
    assert report.capability_summary["failed"] == 0
    assert report.cleanup_summary["duplicate_managers_found"] == 0
    assert report.cleanup_summary["duplicate_runtimes_found"] == 0

    for record in release_3_master_capability_matrix():
        assert record.result == "PASS"
        assert record.exists == "PASS"
        assert record.connected == "PASS"
        assert record.runtime_integrated == "PASS"
        assert record.persistence == "PASS"
        assert record.diagnostics == "PASS"


def test_release_3_batch_g_runtime_project_and_source_compile(tmp_path):
    app = QApplication.instance() or QApplication([])

    compile_start = time.perf_counter()
    report = certify_repository()
    for record in report.source_files:
        if record.path.endswith(".py"):
            py_compile.compile(record.path, doraise=True)
    compile_seconds = time.perf_counter() - compile_start

    startup_start = time.perf_counter()
    window = MainWindow()
    startup_seconds = time.perf_counter() - startup_start

    try:
        workspace = window.canvas.app.workspace
        command_start = time.perf_counter()
        entity = LineEntity(Vector2(0, 0), Vector2(10, 0))
        workspace.command_manager.execute(AddEntityCommand(workspace.entities, entity))
        workspace.selection.select(entity)
        window._commands_changed(workspace.command_manager)
        command_seconds = time.perf_counter() - command_start

        assert workspace.count == 1
        assert workspace.command_manager.undo_count == 1
        assert window.property_panel.workspace is workspace

        render_start = time.perf_counter()
        window.canvas.update()
        window.viewport3d.update()
        app.processEvents()
        render_seconds = time.perf_counter() - render_start

        serializer = ProjectSerializer()
        path = Path(tmp_path) / "batch_g_repository_certification.ksproj"
        save_start = time.perf_counter()
        serializer.save(workspace, path)
        save_seconds = time.perf_counter() - save_start

        load_start = time.perf_counter()
        restored = serializer.load(path)
        load_seconds = time.perf_counter() - load_start
        assert restored.count == 1

        workspace.command_manager.undo()
        assert workspace.count == 0
        workspace.command_manager.redo()
        assert workspace.count == 1

        global LAST_PERFORMANCE_SUMMARY
        LAST_PERFORMANCE_SUMMARY = {
            "compile_seconds": compile_seconds,
            "startup_seconds": startup_seconds,
            "command_seconds": command_seconds,
            "render_seconds": render_seconds,
            "save_seconds": save_seconds,
            "load_seconds": load_seconds,
        }
        assert startup_seconds < 5.0
        assert command_seconds < 1.0
        assert render_seconds < 1.0
        assert save_seconds < 1.0
        assert load_seconds < 1.0

    finally:
        window.close()


if __name__ == "__main__":
    output = Path(".tmp_test_output/release_3_batch_g")
    output.mkdir(parents=True, exist_ok=True)
    test_release_3_batch_g_repository_certification(output)
    test_release_3_batch_g_runtime_project_and_source_compile(output)
    timings = " ".join(
        f"{key}={value:.4f}"
        for key, value in sorted(LAST_PERFORMANCE_SUMMARY.items())
    )
    print(f"release-3-batch-g-repository-certification-ok {timings}")

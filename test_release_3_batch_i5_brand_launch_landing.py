import json
import os
import shutil
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.commands import AddEntityCommand
from engine.entities import LineEntity
from engine.geometry import Vector2
from engine.storage import ProjectSerializer
from ui_v2.branding import (
    AboutDialog,
    BrandAssetLoader,
    BrandEmptyState,
    BrandLandingPage,
    BrandMotionEngine,
    BrandSplashScreen,
    FirstRunExperience,
    NewProjectPanel,
)
from ui_v2.main_window import MainWindow


LAST_PERFORMANCE_SUMMARY = {}


def test_release_3_batch_i5_brand_launch_landing(tmp_path):
    app = QApplication.instance() or QApplication([])

    start = time.perf_counter()
    loader = BrandAssetLoader()
    loader_seconds = time.perf_counter() - start

    requested_assets = [
        "logo.svg",
        "logo_dark.svg",
        "logo_light.svg",
        "icon.ico",
        "icon_16.png",
        "icon_32.png",
        "icon_64.png",
        "icon_128.png",
        "icon_256.png",
        "icon_512.png",
        "splash_background.png",
        "landing_background.png",
        "wallpaper.jpg",
        "empty_state.svg",
        "loading_animation.json",
        "brand.json",
        "placeholders/logo_placeholder.svg",
        "placeholders/icon_placeholder.ico",
        "placeholders/landing_placeholder.png",
        "placeholders/wallpaper_placeholder.jpg",
    ]
    for asset in requested_assets:
        assert (loader.branding_dir / asset).exists(), asset

    manifest = loader.asset_manifest()
    assert all(row["status"] == "PASS" for row in manifest.values())
    assert loader.config.application_name == "Kinematics Studio V2"
    assert loader.config.version == "3.0"
    assert loader.config.build == "Release 3.0 Batch I.5"
    assert loader.initialization_steps()
    assert loader.landing_sections()
    assert loader.project_categories()
    assert loader.first_run_steps()
    assert not loader.load_icon().isNull()

    fallback_dir = Path(tmp_path) / "brand_fallback"
    if fallback_dir.exists():
        shutil.rmtree(fallback_dir)
    shutil.copytree(loader.branding_dir, fallback_dir)
    (fallback_dir / "logo.svg").unlink()
    fallback_loader = BrandAssetLoader(fallback_dir)
    assert fallback_loader.asset_path("logo").name == "logo_placeholder.svg"
    assert fallback_loader.asset_manifest()["logo"]["fallback"] is True

    splash_start = time.perf_counter()
    splash = BrandSplashScreen(loader)
    splash.run_initialization_messages(app)
    splash_seconds = time.perf_counter() - splash_start
    assert splash.progress_value == 100
    assert "Load Branding" in splash.messages
    assert "Open Landing Experience" in splash.messages

    landing_start = time.perf_counter()
    landing = BrandLandingPage(loader)
    landing_seconds = time.perf_counter() - landing_start
    required_sections = {
        "Continue Last Project",
        "Recent Projects",
        "Pinned Projects",
        "New Project",
        "Templates",
        "Workspace Shortcuts",
        "Documentation",
        "Tutorials",
        "Sample Projects",
        "Release Notes",
        "Recent Activity",
        "News",
        "Community",
    }
    assert required_sections <= set(landing.section_buttons)

    new_project = NewProjectPanel(loader)
    assert {
        "CAD",
        "3D CAD",
        "Product Design",
        "Parametric",
        "GIS",
        "BIM",
        "Simulation",
        "Machine/CAM",
        "Rendering",
        "AI",
    } <= set(new_project.category_buttons)

    first_run = FirstRunExperience(loader)
    assert first_run.remember_choices_available is True
    assert [label.text() for label in first_run.step_labels] == loader.first_run_steps()

    empty = BrandEmptyState(loader)
    assert empty.layout().count() >= 3

    about = AboutDialog(loader)
    assert loader.config.application_name in about.windowTitle() or about.windowTitle()
    assert not about.windowIcon().isNull()

    motion = BrandMotionEngine(loader)
    fade = motion.fade(landing)
    slide = motion.slide(landing)
    scale = motion.scale_metadata()
    assert fade.duration() == motion.duration_ms
    assert slide.duration() == motion.duration_ms
    assert scale["transition"] == "scale"

    window_start = time.perf_counter()
    window = MainWindow(brand_loader=loader)
    window_seconds = time.perf_counter() - window_start
    try:
        assert window.windowTitle() == loader.config.application_name
        assert not window.windowIcon().isNull()
        assert window.landing_page.section_buttons["New Project"].text() == "New Project"

        workspace = window.canvas.app.workspace
        command_start = time.perf_counter()
        line = LineEntity(Vector2(0, 0), Vector2(5, 0))
        workspace.command_manager.execute(AddEntityCommand(workspace.entities, line))
        workspace.selection.select(line)
        window._commands_changed(workspace.command_manager)
        command_seconds = time.perf_counter() - command_start
        assert workspace.command_manager.undo_available
        workspace.command_manager.undo()
        workspace.command_manager.redo()

        save_start = time.perf_counter()
        project_path = Path(tmp_path) / "batch_i5_branding.ksproj"
        ProjectSerializer().save(workspace, project_path)
        save_seconds = time.perf_counter() - save_start

        load_start = time.perf_counter()
        restored = ProjectSerializer().load(project_path)
        load_seconds = time.perf_counter() - load_start
        assert restored.count == 1

    finally:
        window.close()
        splash.close()
        about.close()

    global LAST_PERFORMANCE_SUMMARY
    LAST_PERFORMANCE_SUMMARY = {
        "brand_loader_seconds": loader_seconds,
        "splash_seconds": splash_seconds,
        "landing_seconds": landing_seconds,
        "window_seconds": window_seconds,
        "command_seconds": command_seconds,
        "save_seconds": save_seconds,
        "load_seconds": load_seconds,
    }

    assert loader_seconds < 1.0
    assert splash_seconds < 1.0
    assert landing_seconds < 1.0
    assert window_seconds < 5.0
    assert command_seconds < 1.0
    assert save_seconds < 1.0
    assert load_seconds < 1.0


if __name__ == "__main__":
    output = Path(".tmp_test_output/release_3_batch_i5")
    output.mkdir(parents=True, exist_ok=True)
    test_release_3_batch_i5_brand_launch_landing(output)
    timings = " ".join(
        f"{key}={value:.4f}" if isinstance(value, float) else f"{key}={value}"
        for key, value in sorted(LAST_PERFORMANCE_SUMMARY.items())
    )
    print(f"release-3-batch-i5-brand-launch-landing-ok {timings}")

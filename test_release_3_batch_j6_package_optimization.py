import json
import os
import subprocess
import zipfile
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


ORIGINAL_PORTABLE_BYTES = 1_637_757_946
LAST_OPTIMIZATION_SUMMARY = {}


def _run_hidden(command, cwd, timeout=120):
    startupinfo = None
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        timeout=timeout,
        startupinfo=startupinfo,
        env=env,
    )


def test_release_3_batch_j6_package_optimization_contract():
    root = Path("Release_3.0_RC1")
    app_root = root / "macOS" / "KinematicsStudio.app" / "Contents" / "Resources" / "KinematicsStudio"
    portable = root / "Windows" / "Portable.zip"
    manifest_path = root / "BuildInfo" / "BuildManifest.json"

    assert app_root.exists()
    assert portable.exists()
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["dependency_audit"]["status"] == "PASS"
    assert manifest["resource_audit"]["status"] == "PASS"
    assert manifest["dependency_audit"]["forbidden_present"] == []
    assert manifest["runtime"]["global_python_required"] is False
    assert manifest["runtime"]["path_required"] is False
    assert manifest["runtime"]["pip_required"] is False
    assert manifest["runtime"]["venv_required"] is False

    forbidden_paths = [
        app_root / "Runtime" / "Python" / "Lib" / "site-packages",
        app_root / "Runtime" / "site-packages" / "PySide6" / "resources" / "qtwebengine_devtools_resources.debug.pak",
        app_root / "Runtime" / "site-packages" / "PySide6" / "resources" / "v8_context_snapshot.debug.bin",
        app_root / "KinematicsStudio.cs",
        app_root / "KinematicsStudio.compile.ps1",
    ]
    assert not any(path.exists() for path in forbidden_paths)

    packaged_files = [path for path in app_root.rglob("*") if path.is_file()]
    relative_names = [path.relative_to(app_root).as_posix() for path in packaged_files]
    assert not any("__pycache__/" in name or name.endswith((".pyc", ".pyo")) for name in relative_names)
    assert not any("/node_modules/" in name for name in relative_names)
    assert not any("/tests/" in name or Path(name).name.startswith("test_") for name in relative_names)

    assert portable.stat().st_size < ORIGINAL_PORTABLE_BYTES
    assert zipfile.is_zipfile(portable)
    with zipfile.ZipFile(portable) as archive:
        names = archive.namelist()
        assert "KinematicsStudio/Runtime/Python/Lib/site-packages/" not in names
        assert not any(name.startswith("KinematicsStudio/Runtime/Python/Lib/site-packages/") for name in names)
        assert not any("__pycache__/" in name or name.endswith((".pyc", ".pyo")) for name in names)
        assert not any("/node_modules/" in name for name in names)
        assert not any("/tests/" in name or Path(name).name.startswith("test_") for name in names)

    launcher = app_root / "KinematicsStudio.exe"
    runtime_python = app_root / "Runtime" / "Python" / "python.exe"
    launcher_self_test = _run_hidden([str(launcher.resolve()), "--self-test"], app_root.resolve())
    assert launcher_self_test.returncode == 0, launcher_self_test.stderr or launcher_self_test.stdout

    runtime_smoke = _run_hidden(
        [
            str(runtime_python.resolve()),
            "-c",
            (
                "import PySide6, numpy, shiboken6, ui_v2.branding, ui_v2.main_window; "
                "from pathlib import Path; "
                "assert Path('assets/branding/brand.json').exists(); "
                "print('optimized-runtime-ok')"
            ),
        ],
        app_root.resolve(),
    )
    assert runtime_smoke.returncode == 0, runtime_smoke.stderr or runtime_smoke.stdout

    global LAST_OPTIMIZATION_SUMMARY
    LAST_OPTIMIZATION_SUMMARY = {
        "original_portable_bytes": ORIGINAL_PORTABLE_BYTES,
        "optimized_portable_bytes": portable.stat().st_size,
        "space_saved": ORIGINAL_PORTABLE_BYTES - portable.stat().st_size,
        "file_count": len(packaged_files),
    }


if __name__ == "__main__":
    test_release_3_batch_j6_package_optimization_contract()
    summary = " ".join(f"{key}={value}" for key, value in sorted(LAST_OPTIMIZATION_SUMMARY.items()))
    print(f"release-3-batch-j6-package-optimization-ok {summary}")

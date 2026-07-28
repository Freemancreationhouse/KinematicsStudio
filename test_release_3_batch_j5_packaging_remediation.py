import json
import os
import subprocess
import zipfile
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


LAST_VALIDATION_SUMMARY = {}


def _run_hidden(command, cwd):
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
        timeout=120,
        startupinfo=startupinfo,
        env=env,
    )


def test_release_3_batch_j5_packaging_remediation_artifacts_are_self_contained():
    root = Path("Release_3.0_RC1")
    windows = root / "Windows"
    macos_app_resources = root / "macOS" / "KinematicsStudio.app" / "Contents" / "Resources" / "KinematicsStudio"
    portable = windows / "Portable.zip"
    setup = windows / "Setup.exe"
    manifest_path = root / "BuildInfo" / "BuildManifest.json"
    checksums = root / "Checksums" / "SHA256.txt"

    assert portable.exists()
    assert portable.stat().st_size > 100_000_000
    assert zipfile.is_zipfile(portable)
    assert setup.exists()
    assert setup.stat().st_size > 0
    assert manifest_path.exists()
    assert checksums.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["runtime"]["global_python_required"] is False
    assert manifest["runtime"]["path_required"] is False
    assert manifest["runtime"]["pip_required"] is False
    assert manifest["runtime"]["venv_required"] is False
    assert manifest["dependency_audit"]["status"] == "PASS"
    assert manifest["resource_audit"]["status"] == "PASS"

    with zipfile.ZipFile(portable) as archive:
        names = set(archive.namelist())
        required = {
            "KinematicsStudio/KinematicsStudio.exe",
            "KinematicsStudio/KinematicsStudio.bat",
            "KinematicsStudio/main_v2.py",
            "KinematicsStudio/Runtime/Python/python.exe",
            "KinematicsStudio/assets/branding/brand.json",
            "KinematicsStudio/assets/branding/logo.svg",
            "KinematicsStudio/assets/branding/icon.ico",
        }
        assert required.issubset(names)
        assert any(name.startswith("KinematicsStudio/Runtime/site-packages/PySide6/plugins/") for name in names)
        assert any(name.startswith("KinematicsStudio/Runtime/site-packages/shiboken6/") for name in names)
        assert any(name.startswith("KinematicsStudio/Runtime/site-packages/numpy/") for name in names)

    assert (macos_app_resources / "KinematicsStudio.exe").exists()
    assert (macos_app_resources / "Runtime" / "Python" / "python.exe").exists()
    assert (macos_app_resources / "Runtime" / "site-packages" / "PySide6").exists()
    assert (macos_app_resources / "assets" / "branding" / "brand.json").exists()

    setup_self_test = _run_hidden([str(setup.resolve()), "--self-test"], windows.resolve())
    assert setup_self_test.returncode == 0, setup_self_test.stderr or setup_self_test.stdout

    launcher = macos_app_resources / "KinematicsStudio.exe"
    launcher_self_test = _run_hidden([str(launcher.resolve()), "--self-test"], macos_app_resources.resolve())
    assert launcher_self_test.returncode == 0, launcher_self_test.stderr or launcher_self_test.stdout

    runtime_python = macos_app_resources / "Runtime" / "Python" / "python.exe"
    runtime_smoke = _run_hidden(
        [
            str(runtime_python.resolve()),
            "-c",
            "import sys, PySide6, numpy, ui_v2.branding; from pathlib import Path; assert Path('assets/branding/brand.json').exists(); print(sys.executable)",
        ],
        macos_app_resources.resolve(),
    )
    assert runtime_smoke.returncode == 0, runtime_smoke.stderr or runtime_smoke.stdout
    assert "Runtime" in runtime_smoke.stdout

    checksum_text = checksums.read_text(encoding="utf-8")
    assert "Windows/Setup.exe" in checksum_text
    assert "Windows/Portable.zip" in checksum_text
    assert "BuildInfo/BuildManifest.json" in checksum_text

    global LAST_VALIDATION_SUMMARY
    LAST_VALIDATION_SUMMARY = {
        "portable_bytes": portable.stat().st_size,
        "setup_bytes": setup.stat().st_size,
        "setup_self_test": setup_self_test.returncode,
        "launcher_self_test": launcher_self_test.returncode,
        "runtime_smoke": runtime_smoke.returncode,
    }


if __name__ == "__main__":
    test_release_3_batch_j5_packaging_remediation_artifacts_are_self_contained()
    summary = " ".join(f"{key}={value}" for key, value in sorted(LAST_VALIDATION_SUMMARY.items()))
    print(f"release-3-batch-j5-packaging-remediation-ok {summary}")

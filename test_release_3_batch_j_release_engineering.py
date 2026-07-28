import json
import os
import time
import zipfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from tools.release.build_release import ReleaseBuilder


LAST_BUILD_SUMMARY = {}


def test_release_3_batch_j_release_engineering_pipeline():
    start = time.perf_counter()
    builder = ReleaseBuilder(clean=True)
    manifest = builder.build()
    build_seconds = time.perf_counter() - start

    root = Path("Release_3.0_RC1")
    windows = root / "Windows"
    macos = root / "macOS"
    docs = root / "Documentation"
    checksums = root / "Checksums" / "SHA256.txt"
    build_manifest = root / "BuildInfo" / "BuildManifest.json"
    version = root / "BuildInfo" / "Version.json"

    assert (windows / "Setup.exe").exists()
    assert (windows / "Setup.exe").stat().st_size > 0
    assert (windows / "Portable.zip").exists()
    assert zipfile.is_zipfile(windows / "Portable.zip")
    with zipfile.ZipFile(windows / "Portable.zip") as archive:
        names = set(archive.namelist())
        assert "KinematicsStudio/main_v2.py" in names
        assert "KinematicsStudio/assets/branding/brand.json" in names
        assert "KinematicsStudio/KinematicsStudio.bat" in names
        assert "KinematicsStudio/KinematicsStudio.exe" in names
        assert "KinematicsStudio/Runtime/Python/python.exe" in names
        assert any(name.startswith("KinematicsStudio/Runtime/site-packages/PySide6/") for name in names)
        assert any(name.startswith("KinematicsStudio/Runtime/site-packages/shiboken6/") for name in names)
        assert any(name.startswith("KinematicsStudio/Runtime/site-packages/numpy/") for name in names)

    assert (macos / "KinematicsStudio.app" / "Contents" / "Info.plist").exists()
    assert (macos / "KinematicsStudio.app" / "Contents" / "MacOS" / "KinematicsStudio").exists()
    assert (macos / "KinematicsStudio.app" / "Contents" / "Resources" / "KinematicsStudio" / "main_v2.py").exists()

    assert (docs / "ReleaseNotes.pdf").exists()
    assert (docs / "InstallationGuide.pdf").exists()
    assert (docs / "UserGuide.pdf").exists()
    assert (docs / "License.txt").exists()

    assert version.exists()
    version_data = json.loads(version.read_text(encoding="utf-8"))
    assert version_data["release"] == "3.0"
    assert version_data["batch"] == "J"
    assert version_data["channel"] == "RC1"
    assert version_data["git_commit"]

    assert build_manifest.exists()
    manifest_data = json.loads(build_manifest.read_text(encoding="utf-8"))
    assert manifest_data["application"]["release"] == "3.0"
    assert manifest_data["runtime"]["global_python_required"] is False
    assert manifest_data["runtime"]["path_required"] is False
    assert manifest_data["runtime"]["pip_required"] is False
    assert manifest_data["runtime"]["venv_required"] is False
    assert manifest_data["dependency_audit"]["status"] == "PASS"
    assert manifest_data["resource_audit"]["status"] == "PASS"
    assert any(item["type"] == "windows_setup_exe" and item["status"] == "PASS" for item in manifest_data["artifacts"])
    assert any(item["type"] == "windows_portable_zip" and item["status"] == "PASS" for item in manifest_data["artifacts"])
    assert any(item["type"] == "macos_app_bundle" and item["status"] == "PASS" for item in manifest_data["artifacts"])

    msi = windows / "KinematicsStudio.msi"
    msi_unsupported = windows / "KinematicsStudio.msi.unsupported.json"
    assert msi.exists() or msi_unsupported.exists()

    dmg = macos / "KinematicsStudio.dmg"
    dmg_unsupported = macos / "KinematicsStudio.dmg.unsupported.json"
    assert dmg.exists() or dmg_unsupported.exists()

    assert checksums.exists()
    checksum_text = checksums.read_text(encoding="utf-8")
    assert "Windows/Setup.exe" in checksum_text
    assert "Windows/Portable.zip" in checksum_text
    assert "BuildInfo/Version.json" in checksum_text

    assert not (root / "_staging").exists()
    assert not (windows / "_setup_payload").exists()

    global LAST_BUILD_SUMMARY
    LAST_BUILD_SUMMARY = {
        "build_seconds": build_seconds,
        "artifacts": len(manifest["artifacts"]),
        "unsupported": len(manifest["unsupported"]),
        "setup_bytes": (windows / "Setup.exe").stat().st_size,
        "portable_bytes": (windows / "Portable.zip").stat().st_size,
    }

    assert build_seconds < 600.0


if __name__ == "__main__":
    test_release_3_batch_j_release_engineering_pipeline()
    timings = " ".join(
        f"{key}={value:.4f}" if isinstance(value, float) else f"{key}={value}"
        for key, value in sorted(LAST_BUILD_SUMMARY.items())
    )
    print(f"release-3-batch-j-release-engineering-ok {timings}")

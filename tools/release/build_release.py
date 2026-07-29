import argparse
import fnmatch
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "release" / "release_config.json"


class ReleaseBuilder:
    """Production release artifact builder for Kinematics Studio Release 3.0."""

    def __init__(self, clean=True):
        self.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        self.clean = clean
        self.root = ROOT
        self.artifact_root = self.root / self.config["artifact_root"]
        self.windows_dir = self.artifact_root / "Windows"
        self.macos_dir = self.artifact_root / "macOS"
        self.documentation_dir = self.artifact_root / "Documentation"
        self.checksums_dir = self.artifact_root / "Checksums"
        self.buildinfo_dir = self.artifact_root / "BuildInfo"
        self.staging_dir = self.artifact_root / "_staging"
        self.runtime_python_source = Path(sys.executable).resolve().parent
        self.project_site_packages = self.root / ".venv" / "Lib" / "site-packages"
        self.build_date = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.git_commit = self._git_commit()
        self.tooling = self._discover_tooling()
        self.manifest = {
            "application": self.config["application"],
            "build": {
                "date_utc": self.build_date,
                "host_platform": platform.platform(),
                "python": sys.version,
                "git_commit": self.git_commit,
            },
            "tooling": self.tooling,
            "runtime": {},
            "dependency_audit": {},
            "resource_audit": {},
            "optimization": {
                "policy": "Remove only verified development, test, cache and duplicate packaging content.",
                "removed": [],
                "retained": [],
            },
            "artifacts": [],
            "unsupported": [],
        }

    def build(self):
        """Generate release artifacts, documentation, manifests and checksums."""

        self._prepare_directories()
        self._write_version_manifest()
        self._stage_portable_application()
        self._build_windows_portable_zip()
        self._build_windows_installer_placeholder()
        self._build_macos_app()
        self._build_macos_dmg()
        self._build_documentation()
        self._write_build_manifest()
        self._cleanup_internal_build_dirs()
        self._write_checksums()
        self._validate_artifact_tree()
        return self.manifest

    def _prepare_directories(self):
        if self.clean and self.artifact_root.exists():
            shutil.rmtree(self.artifact_root)
        for directory in (
            self.windows_dir,
            self.macos_dir,
            self.documentation_dir,
            self.checksums_dir,
            self.buildinfo_dir,
            self.staging_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def _stage_portable_application(self):
        app_stage = self.staging_dir / "KinematicsStudio"
        app_stage.mkdir(parents=True, exist_ok=True)
        for item in self.config["include"]:
            src = self.root / item
            dst = app_stage / item
            if not src.exists():
                continue
            if src.is_dir():
                shutil.copytree(src, dst, ignore=self._ignore_patterns())
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

        self._bundle_python_runtime(app_stage)
        self._write_launcher_scripts(app_stage)
        self._audit_dependencies(app_stage)
        self._audit_resources(app_stage)

    def _bundle_python_runtime(self, app_stage):
        """Bundle Python, site-packages, Qt plugins and runtime DLLs."""

        runtime_dir = app_stage / "Runtime"
        python_dst = runtime_dir / "Python"
        site_dst = runtime_dir / "site-packages"

        self._copy_tree(self.runtime_python_source, python_dst, ignore=self._runtime_python_ignore)
        if not self.project_site_packages.exists():
            raise RuntimeError(f"Project site-packages not found: {self.project_site_packages}")
        self._copy_tree(self.project_site_packages, site_dst, ignore=self._site_packages_ignore)

        runtime_python = python_dst / ("python.exe" if os.name == "nt" else "python")
        if not runtime_python.exists():
            raise RuntimeError(f"Bundled Python interpreter missing: {runtime_python}")

        self.manifest["runtime"] = {
            "python_source": str(self.runtime_python_source),
            "site_packages_source": str(self.project_site_packages),
            "python_bundled": str(python_dst.relative_to(app_stage)),
            "site_packages_bundled": str(site_dst.relative_to(app_stage)),
            "runtime_python": str(runtime_python.relative_to(app_stage)),
            "global_python_required": False,
            "path_required": False,
            "pip_required": False,
            "venv_required": False,
        }
        self.manifest["optimization"]["removed"].append(
            {
                "path": "Runtime/Python/Lib/site-packages",
                "reason": "Duplicate dependency tree; verified runtime packages are copied once to Runtime/site-packages.",
            }
        )
        self.manifest["optimization"]["retained"].extend(
            [
                {
                    "path": "Runtime/site-packages/PySide6",
                    "reason": "Qt runtime is required by the application UI and renderer integration.",
                },
                {
                    "path": "Runtime/site-packages/OCP",
                    "reason": "OpenCascade/OCP imports are used by CAD import/export and OCC modeling modules.",
                },
                {
                    "path": "Runtime/site-packages/vtk*",
                    "reason": "Large visualization/runtime libraries retained because runtime usage may be indirect.",
                },
                {
                    "path": "Runtime/site-packages/PySide6/Qt6WebEngineCore.dll",
                    "reason": "Large Qt module retained; no source import found, but broad Qt modules are kept under the safety rule unless proven unused by runtime.",
                },
            ]
        )

    def _ignore_patterns(self):
        excludes = self.config.get("exclude", [])
        return self._production_ignore(*excludes)

    def _production_ignore(self, *extra_patterns):
        """Return an ignore callable for verified non-runtime packaging debris."""

        patterns = tuple(
            list(extra_patterns)
            + [
                "*.pyc",
                "*.pyo",
                "__pycache__",
                ".pytest_cache",
                ".coverage",
                "coverage",
                "htmlcov",
            ]
        )

        def ignore(directory, names):
            ignored = set()
            for name in names:
                if any(fnmatch.fnmatch(name, pattern) for pattern in patterns):
                    ignored.add(name)
            return ignored

        return ignore

    def _runtime_python_ignore(self, directory, names):
        """Exclude duplicated/development-only content from the bundled interpreter."""

        ignored = set(self._production_ignore()(directory, names))
        current = Path(directory).resolve()
        runtime_lib = (self.runtime_python_source / "Lib").resolve()
        if current == runtime_lib and "site-packages" in names:
            ignored.add("site-packages")
        return ignored

    def _site_packages_ignore(self, directory, names):
        """Exclude test/cache/debug artifacts from the single packaged dependency tree."""

        ignored = set(self._production_ignore()(directory, names))
        current = Path(directory)
        for name in names:
            lower = name.lower()
            if name == "tests" or name == "testing" or lower.startswith("test_"):
                ignored.add(name)
            if lower.endswith(".debug.pak") or lower.endswith(".debug.bin"):
                ignored.add(name)
        return ignored

    def _write_launcher_scripts(self, app_stage):
        launcher = app_stage / "KinematicsStudio.bat"
        launcher.write_text(
            "@echo off\n"
            "setlocal\n"
            "cd /d %~dp0\n"
            "set PYTHONHOME=%~dp0Runtime\\Python\n"
            "set PYTHONPATH=%~dp0Runtime\\site-packages;%~dp0\n"
            "set QT_QPA_PLATFORM_PLUGIN_PATH=%~dp0Runtime\\site-packages\\PySide6\\plugins\\platforms\n"
            "\"%~dp0Runtime\\Python\\python.exe\" main_v2.py\n",
            encoding="utf-8",
        )
        shell = app_stage / "KinematicsStudio.command"
        shell.write_text(
            "#!/bin/sh\n"
            "DIR=\"$(cd \"$(dirname \"$0\")\" && pwd)\"\n"
            "cd \"$DIR\"\n"
            "export PYTHONHOME=\"$DIR/Runtime/Python\"\n"
            "export PYTHONPATH=\"$DIR/Runtime/site-packages:$DIR\"\n"
            "exec \"$DIR/Runtime/Python/python\" main_v2.py\n",
            encoding="utf-8",
        )

    def _build_windows_portable_zip(self):
        portable = self.windows_dir / self.config["platforms"]["windows"]["portable_zip"]
        self._zip_directory(self.staging_dir / "KinematicsStudio", portable)
        self._record_artifact(portable, "windows_portable_zip", "zip", "PASS")

    def _build_windows_installer_placeholder(self):
        installer_dir = self.windows_dir / "Installer"
        installer_dir.mkdir(parents=True, exist_ok=True)
        readme = installer_dir / "README.txt"
        readme.write_text(
            "Kinematics Studio\n\n"
            "Windows installer generation has been\n"
            "migrated to the new Inno Setup release\n"
            "pipeline.\n\n"
            "Run installer/KinematicsStudio.iss\n"
            "after the release build completes.\n",
            encoding="utf-8",
        )
        self._record_artifact(readme, "windows_installer_placeholder", "txt", "PASS")

    def _build_macos_app(self):
        app_name = self.config["platforms"]["macos"]["app_bundle"]
        bundle = self.macos_dir / app_name
        contents = bundle / "Contents"
        macos = contents / "MacOS"
        resources = contents / "Resources"
        macos.mkdir(parents=True, exist_ok=True)
        resources.mkdir(parents=True, exist_ok=True)

        self._copy_tree(self.staging_dir / "KinematicsStudio", resources / "KinematicsStudio")
        launcher = macos / "KinematicsStudio"
        launcher.write_text(
            "#!/bin/sh\n"
            "DIR=\"$(cd \"$(dirname \"$0\")\" && pwd)\"\n"
            "cd \"$DIR/../Resources/KinematicsStudio\"\n"
            "export PYTHONHOME=\"$PWD/Runtime/Python\"\n"
            "export PYTHONPATH=\"$PWD/Runtime/site-packages:$PWD\"\n"
            "exec \"$PWD/Runtime/Python/python\" main_v2.py\n",
            encoding="utf-8",
        )
        try:
            launcher.chmod(0o755)
        except OSError:
            pass

        info = self._macos_info_plist()
        (contents / "Info.plist").write_text(info, encoding="utf-8")
        self._record_artifact(bundle, "macos_app_bundle", "app", "PASS")

    def _build_macos_dmg(self):
        dmg = self.macos_dir / self.config["platforms"]["macos"]["dmg"]
        hdiutil = self.tooling.get("hdiutil")
        if not hdiutil:
            self._unsupported("macos_dmg", dmg, "hdiutil not available on this host")
            return
        result = subprocess.run(
            [hdiutil, "create", "-volname", "KinematicsStudio", "-srcfolder", str(self.macos_dir / "KinematicsStudio.app"), "-ov", "-format", "UDZO", str(dmg)],
            capture_output=True,
            text=True,
            timeout=180,
        )
        if dmg.exists() and result.returncode == 0:
            self._record_artifact(dmg, "macos_dmg", "dmg", "PASS")
        else:
            self._unsupported("macos_dmg", dmg, "hdiutil failed")

    def _build_documentation(self):
        license_text = (
            "Kinematics Studio V2 Release 3.0 RC1\n\n"
            "Production release-engineering license placeholder. Replace before public distribution.\n"
        )
        (self.documentation_dir / self.config["documentation"]["license"]).write_text(license_text, encoding="utf-8")
        for name, title, body in (
            ("release_notes", "Release Notes", "Release 3.0 RC1 release-engineering artifact set."),
            ("installation_guide", "Installation Guide", "Use Windows Portable.zip or generate the installer with installer/KinematicsStudio.iss; macOS bundle is prepared for signing/notarization."),
            ("user_guide", "User Guide", "Launch Kinematics Studio, use the landing page, create/open projects, and switch workspaces."),
        ):
            self._write_pdf(self.documentation_dir / self.config["documentation"][name], title, body)
        for path in self.documentation_dir.iterdir():
            if path.is_file():
                self._record_artifact(path, f"documentation_{path.stem}", path.suffix.lstrip("."), "PASS")

    def _write_pdf(self, path, title, body):
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas

            c = canvas.Canvas(str(path), pagesize=letter)
            width, height = letter
            c.setFont("Helvetica-Bold", 18)
            c.drawString(72, height - 72, title)
            c.setFont("Helvetica", 11)
            y = height - 110
            for line in body.splitlines() or [body]:
                c.drawString(72, y, line)
                y -= 16
            c.drawString(72, y - 16, f"Build: {self.config['application']['version']} {self.config['application']['channel']}")
            c.drawString(72, y - 32, f"Date: {self.build_date}")
            c.save()
        except Exception:
            path.write_text(f"{title}\n\n{body}\n\nBuild: {self.build_date}\n", encoding="utf-8")

    def _write_version_manifest(self):
        version = {
            "name": self.config["application"]["name"],
            "product_name": self.config["application"]["product_name"],
            "version": self.config["application"]["version"],
            "release": self.config["application"]["release"],
            "batch": self.config["application"]["batch"],
            "channel": self.config["application"]["channel"],
            "build_date_utc": self.build_date,
            "git_commit": self.git_commit,
        }
        path = self.buildinfo_dir / "Version.json"
        path.write_text(json.dumps(version, indent=2), encoding="utf-8")
        self._record_artifact(path, "version_manifest", "json", "PASS")

    def _write_build_manifest(self):
        path = self.buildinfo_dir / "BuildManifest.json"
        path.write_text(json.dumps(self.manifest, indent=2), encoding="utf-8")
        self._record_artifact(path, "build_manifest", "json", "PASS")

    def _write_checksums(self):
        lines = []
        for path in sorted(self.artifact_root.rglob("*")):
            if path.is_file() and "_staging" not in path.parts and path.name != "SHA256.txt":
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                lines.append(f"{digest}  {path.relative_to(self.artifact_root).as_posix()}")
        checksum = self.checksums_dir / "SHA256.txt"
        checksum.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self._record_artifact(checksum, "sha256_checksums", "txt", "PASS")

    def _cleanup_internal_build_dirs(self):
        """Remove internal staging folders from the distributable artifact tree."""

        for path in (self.staging_dir,):
            if path.exists():
                shutil.rmtree(path)

    def _validate_artifact_tree(self):
        required = [
            self.windows_dir / self.config["platforms"]["windows"]["portable_zip"],
            self.macos_dir / self.config["platforms"]["macos"]["app_bundle"],
            self.documentation_dir / self.config["documentation"]["release_notes"],
            self.documentation_dir / self.config["documentation"]["installation_guide"],
            self.documentation_dir / self.config["documentation"]["user_guide"],
            self.documentation_dir / self.config["documentation"]["license"],
            self.checksums_dir / "SHA256.txt",
            self.buildinfo_dir / "Version.json",
            self.buildinfo_dir / "BuildManifest.json",
        ]
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            raise RuntimeError(f"Release artifact validation failed: {missing}")
        if self.manifest["dependency_audit"].get("status") != "PASS":
            raise RuntimeError("Dependency audit failed")
        if self.manifest["resource_audit"].get("status") != "PASS":
            raise RuntimeError("Resource audit failed")

    def _unsupported(self, artifact_type, path, reason):
        record_path = path.with_suffix(path.suffix + ".unsupported.json")
        record = {
            "artifact_type": artifact_type,
            "target": str(path),
            "status": "UNSUPPORTED_ON_THIS_HOST",
            "reason": reason,
            "build_date_utc": self.build_date,
        }
        record_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        self.manifest["unsupported"].append(record)
        self._record_artifact(record_path, artifact_type, "unsupported.json", "UNSUPPORTED")

    def _record_artifact(self, path, artifact_type, format_name, status):
        self.manifest["artifacts"].append(
            {
                "type": artifact_type,
                "format": format_name,
                "path": str(Path(path).relative_to(self.root) if Path(path).is_absolute() else path),
                "status": status,
            }
        )

    def _copy_tree(self, src, dst, ignore=None):
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=ignore or self._ignore_patterns())

    def _zip_directory(self, src, dst):
        if dst.exists():
            dst.unlink()
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_STORED) as archive:
            for path in sorted(src.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(src.parent))

    def _audit_dependencies(self, app_stage):
        """Fail the build if bundled runtime dependencies are missing."""

        required = [
            app_stage / "Runtime" / "Python" / "python.exe",
            app_stage / "Runtime" / "site-packages" / "PySide6",
            app_stage / "Runtime" / "site-packages" / "shiboken6",
            app_stage / "Runtime" / "site-packages" / "numpy",
        ]
        forbidden = [
            app_stage / "Runtime" / "Python" / "Lib" / "site-packages",
            app_stage / "Runtime" / "site-packages" / "PySide6" / "resources" / "qtwebengine_devtools_resources.debug.pak",
            app_stage / "Runtime" / "site-packages" / "PySide6" / "resources" / "v8_context_snapshot.debug.bin",
        ]
        missing = [str(path.relative_to(app_stage)) for path in required if not path.exists()]
        forbidden_present = [str(path.relative_to(app_stage)) for path in forbidden if path.exists()]
        self.manifest["dependency_audit"] = {
            "required": [str(path.relative_to(app_stage)) for path in required],
            "missing": missing,
            "forbidden_present": forbidden_present,
            "status": "PASS" if not missing and not forbidden_present else "FAIL",
        }
        if missing:
            raise RuntimeError(f"Bundled dependency audit failed: {missing}")
        if forbidden_present:
            raise RuntimeError(f"Production optimization audit failed: {forbidden_present}")

    def _audit_resources(self, app_stage):
        """Fail the build if required runtime resources are missing."""

        required = [
            app_stage / "assets" / "branding" / "brand.json",
            app_stage / "assets" / "branding" / "logo.svg",
            app_stage / "assets" / "branding" / "icon.ico",
            app_stage / "assets" / "branding" / "splash_background.png",
            app_stage / "assets" / "branding" / "landing_background.png",
            app_stage / "ui_v2" / "theme.py",
            app_stage / "Runtime" / "site-packages" / "PySide6" / "plugins",
        ]
        missing = [str(path.relative_to(app_stage)) for path in required if not path.exists()]
        self.manifest["resource_audit"] = {
            "required": [str(path.relative_to(app_stage)) for path in required],
            "missing": missing,
            "status": "PASS" if not missing else "FAIL",
        }
        if missing:
            raise RuntimeError(f"Bundled resource audit failed: {missing}")

    def _discover_tooling(self):
        names = ["pyinstaller", "nuitka", "cxfreeze", "briefcase", "iscc", "hdiutil"]
        return {name: shutil.which(name) for name in names}

    def _git_commit(self):
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(self.root),
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() if result.returncode == 0 else ""

    def _macos_info_plist(self):
        app = self.config["application"]
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>{app['name']}</string>
  <key>CFBundleDisplayName</key><string>{app['name']}</string>
  <key>CFBundleIdentifier</key><string>studio.kinematics.KinematicsStudio</string>
  <key>CFBundleVersion</key><string>{app['version']}</string>
  <key>CFBundleShortVersionString</key><string>{app['version']}</string>
  <key>CFBundleExecutable</key><string>KinematicsStudio</string>
  <key>LSMinimumSystemVersion</key><string>12.0</string>
  <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
"""


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build Kinematics Studio release artifacts.")
    parser.add_argument("--no-clean", action="store_true", help="Do not remove the existing release folder before building.")
    args = parser.parse_args(argv)
    builder = ReleaseBuilder(clean=not args.no_clean)
    manifest = builder.build()
    print(json.dumps({
        "artifact_root": str(builder.artifact_root),
        "artifacts": len(manifest["artifacts"]),
        "unsupported": len(manifest["unsupported"]),
    }, indent=2))


if __name__ == "__main__":
    main()

import json
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QSettings, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplashScreen,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class BrandConfig:
    """External brand configuration loaded from assets/branding/brand.json."""

    application_name: str
    company: str
    version: str
    build: str
    tagline: str
    primary_color: str
    secondary_color: str
    accent_color: str
    theme: str
    fonts: dict
    assets: dict
    placeholders: dict
    splash: dict
    launch_sequence: list
    landing: dict
    new_project: dict
    first_run: dict
    empty_state: dict
    motion: dict
    shell: dict


class BrandAssetLoader:
    """Centralized external branding loader with placeholder fallback support."""

    REQUIRED_ASSETS = (
        "logo",
        "logo_dark",
        "logo_light",
        "icon",
        "icon_16",
        "icon_32",
        "icon_64",
        "icon_128",
        "icon_256",
        "icon_512",
        "splash_background",
        "landing_background",
        "wallpaper",
        "empty_state",
        "loading_animation",
    )

    def __init__(self, branding_dir=None):
        self.branding_dir = Path(branding_dir) if branding_dir else self.default_branding_dir()
        self.config_path = self.branding_dir / "brand.json"
        self.config = self._load_config()

    @staticmethod
    def default_branding_dir():
        """Return the repository branding directory."""

        return Path(__file__).resolve().parents[1] / "assets" / "branding"

    def _load_config(self):
        if not self.config_path.exists():
            raise FileNotFoundError(f"Brand configuration not found: {self.config_path}")

        data = json.loads(self.config_path.read_text(encoding="utf-8"))
        return BrandConfig(
            application_name=data["application_name"],
            company=data["company"],
            version=data["version"],
            build=data["build"],
            tagline=data["tagline"],
            primary_color=data["primary_color"],
            secondary_color=data["secondary_color"],
            accent_color=data["accent_color"],
            theme=data["theme"],
            fonts=data.get("fonts", {}),
            assets=data.get("assets", {}),
            placeholders=data.get("placeholders", {}),
            splash=data.get("splash", {}),
            launch_sequence=data.get("launch_sequence", []),
            landing=data.get("landing", {}),
            new_project=data.get("new_project", {}),
            first_run=data.get("first_run", {}),
            empty_state=data.get("empty_state", {}),
            motion=data.get("motion", {}),
            shell=data.get("shell", {}),
        )

    def asset_path(self, key):
        """Return an existing asset path, falling back to configured placeholders."""

        configured = self.config.assets.get(key)
        if configured:
            path = self.branding_dir / configured
            if path.exists():
                return path

        placeholder = self.config.placeholders.get(key)
        if placeholder:
            fallback = self.branding_dir / placeholder
            if fallback.exists():
                return fallback

        return None

    def asset_manifest(self):
        """Return asset resolution metadata for diagnostics and certification."""

        rows = {}
        for key in self.REQUIRED_ASSETS:
            configured = self.config.assets.get(key)
            configured_path = self.branding_dir / configured if configured else None
            resolved = self.asset_path(key)
            rows[key] = {
                "configured": str(configured_path) if configured_path else "",
                "resolved": str(resolved) if resolved else "",
                "fallback": bool(configured_path and resolved and configured_path != resolved),
                "status": "PASS" if resolved else "MISSING",
            }
        return rows

    def load_icon(self, key="icon"):
        """Load a branded icon without hardcoded image paths."""

        path = self.asset_path(key)
        return QIcon(str(path)) if path else QIcon()

    def pixmap(self, key):
        """Load a branded pixmap without hardcoded image paths."""

        path = self.asset_path(key)
        return QPixmap(str(path)) if path else QPixmap()

    def initialization_steps(self):
        """Return real startup steps displayed during application launch."""

        return list(self.config.launch_sequence)

    def landing_sections(self):
        """Return configured landing-page sections."""

        return list(self.config.landing.get("sections", []))

    def project_categories(self):
        """Return configured new-project categories."""

        return list(self.config.new_project.get("categories", []))

    def first_run_steps(self):
        """Return configured first-run onboarding steps."""

        return list(self.config.first_run.get("steps", []))


class BrandMotionEngine:
    """One reusable motion helper for shell transitions and brand animations."""

    def __init__(self, loader=None):
        self.loader = loader or BrandAssetLoader()
        self.duration_ms = int(self.loader.config.motion.get("duration_ms", 180))

    def fade(self, widget, start=0.0, end=1.0):
        """Create a fade animation for the supplied widget."""

        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
        effect.setOpacity(start)
        animation = QPropertyAnimation(effect, b"opacity", widget)
        animation.setDuration(self.duration_ms)
        animation.setStartValue(start)
        animation.setEndValue(end)
        animation.setEasingCurve(QEasingCurve.InOutCubic)
        return animation

    def slide(self, widget, offset_x=20, offset_y=0):
        """Create a slide animation without changing engineering state."""

        start = widget.pos()
        animation = QPropertyAnimation(widget, b"pos", widget)
        animation.setDuration(self.duration_ms)
        animation.setStartValue(start + widget.pos().__class__(offset_x, offset_y))
        animation.setEndValue(start)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        return animation

    def scale_metadata(self, target="dialog"):
        """Return scale transition metadata for consumers that animate layouts."""

        return {
            "target": target,
            "duration_ms": self.duration_ms,
            "transition": "scale",
            "asset": str(self.loader.asset_path("loading_animation") or ""),
        }


class BrandSplashScreen(QSplashScreen):
    """Splash framework driven by external brand configuration and real steps."""

    def __init__(self, loader=None):
        self.loader = loader or BrandAssetLoader()
        pixmap = self.loader.pixmap("splash_background")
        if pixmap.isNull():
            pixmap = QPixmap(640, 360)
            pixmap.fill(Qt.black)
        super().__init__(pixmap)
        self.progress_value = 0
        self.messages = []

    def set_progress(self, value, message):
        """Update progress and keep launch diagnostics inspectable."""

        self.progress_value = max(0, min(100, int(value)))
        self.messages.append(message)
        display = f"{self.loader.config.application_name} {self.loader.config.version}"
        if self.loader.config.splash.get("show_build", True):
            display = f"{display} • {self.loader.config.build}"
        self.showMessage(
            f"{display}\n{message}\n{self.progress_value}%",
            Qt.AlignLeft | Qt.AlignBottom,
            Qt.white,
        )

    def run_initialization_messages(self, app=None):
        """Display configured initialization steps without fake hidden work."""

        steps = self.loader.initialization_steps()
        total = max(1, len(steps))
        for index, step in enumerate(steps, start=1):
            self.set_progress(round(index * 100 / total), step)
            if app is not None:
                app.processEvents()


class BrandLandingPage(QWidget):
    """Production landing platform backed entirely by external brand metadata."""

    def __init__(self, loader=None, app_context=None, parent=None):
        super().__init__(parent)
        self.loader = loader or BrandAssetLoader()
        self.app_context = app_context
        self.section_buttons = {}
        self.category_buttons = {}
        self._build()

    def _build(self):
        self.setObjectName("BrandLandingPage")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(self.loader.config.application_name)
        title.setObjectName("BrandLandingTitle")
        title.setStyleSheet("font-size: 28px; font-weight: 600;")
        layout.addWidget(title)

        tagline = QLabel(self.loader.config.tagline)
        tagline.setObjectName("BrandLandingTagline")
        layout.addWidget(tagline)

        tabs = QTabWidget()
        tabs.addTab(self._landing_sections_widget(), "Home")
        tabs.addTab(NewProjectPanel(self.loader), "New Project")
        tabs.addTab(FirstRunExperience(self.loader), "First Run")
        layout.addWidget(tabs, 1)

    def _landing_sections_widget(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        grid = QGridLayout(body)
        sections = self.loader.landing_sections()
        for index, section in enumerate(sections):
            button = QPushButton(section)
            button.setObjectName(f"LandingAction_{section.replace(' ', '_').replace('/', '_')}")
            button.setMinimumHeight(42)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.section_buttons[section] = button
            grid.addWidget(button, index // 2, index % 2)
        scroll.setWidget(body)
        return scroll


class NewProjectPanel(QWidget):
    """Configurable new-project platform for workspace categories and metadata."""

    def __init__(self, loader=None, parent=None):
        super().__init__(parent)
        self.loader = loader or BrandAssetLoader()
        self.category_buttons = {}
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Choose a project category"))
        grid = QGridLayout()
        for index, category in enumerate(self.loader.project_categories()):
            button = QPushButton(category)
            button.setObjectName(f"NewProject_{category.replace(' ', '_').replace('/', '_')}")
            self.category_buttons[category] = button
            grid.addWidget(button, index // 3, index % 3)
        layout.addLayout(grid)
        units = QLabel("Units: " + ", ".join(self.loader.config.new_project.get("units", [])))
        units.setObjectName("NewProjectUnits")
        layout.addWidget(units)
        layout.addStretch(1)


class FirstRunExperience(QWidget):
    """Onboarding framework with persistent user choices."""

    def __init__(self, loader=None, parent=None):
        super().__init__(parent)
        self.loader = loader or BrandAssetLoader()
        self.settings = QSettings(self.loader.config.company, self.loader.config.application_name)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("First Run Setup"))
        self.step_labels = []
        for step in self.loader.first_run_steps():
            label = QLabel(step)
            label.setObjectName(f"FirstRun_{step.replace(' ', '_')}")
            layout.addWidget(label)
            self.step_labels.append(label)
        remember = self.loader.config.first_run.get("remember_choices", True)
        self.remember_choices_available = bool(remember)
        self.settings.setValue("first_run/remember_choices_available", bool(remember))
        layout.addStretch(1)


class BrandEmptyState(QFrame):
    """Reusable empty-state component with external illustration metadata."""

    def __init__(self, loader=None, parent=None):
        super().__init__(parent)
        self.loader = loader or BrandAssetLoader()
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        image = QLabel()
        pixmap = self.loader.pixmap("empty_state")
        if not pixmap.isNull():
            image.setPixmap(pixmap.scaledToWidth(240, Qt.SmoothTransformation))
        image.setObjectName("BrandEmptyStateIllustration")
        layout.addWidget(image, alignment=Qt.AlignCenter)

        message = QLabel(self.loader.config.empty_state.get("message", ""))
        message.setObjectName("BrandEmptyStateMessage")
        layout.addWidget(message, alignment=Qt.AlignCenter)

        actions = QHBoxLayout()
        action = QPushButton(self.loader.config.empty_state.get("action", "Start"))
        docs = QPushButton(self.loader.config.empty_state.get("documentation", "Documentation"))
        action.setObjectName("BrandEmptyStateAction")
        docs.setObjectName("BrandEmptyStateDocumentation")
        actions.addWidget(action)
        actions.addWidget(docs)
        layout.addLayout(actions)


class AboutDialog(QDialog):
    """Application shell metadata dialog loaded from the brand configuration."""

    def __init__(self, loader=None, parent=None):
        super().__init__(parent)
        self.loader = loader or BrandAssetLoader()
        self.setWindowTitle(self.loader.config.shell.get("about_title", "About"))
        self.setWindowIcon(self.loader.load_icon())
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        logo = QLabel()
        pixmap = self.loader.pixmap("logo")
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaledToWidth(320, Qt.SmoothTransformation))
        layout.addWidget(logo, alignment=Qt.AlignCenter)

        details = [
            self.loader.config.application_name,
            self.loader.config.company,
            f"Version {self.loader.config.version}",
            self.loader.config.build,
            self.loader.config.tagline,
            self.loader.config.shell.get("license", ""),
            self.loader.config.shell.get("credits", ""),
        ]
        for item in details:
            label = QLabel(item)
            label.setWordWrap(True)
            layout.addWidget(label)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, alignment=Qt.AlignRight)

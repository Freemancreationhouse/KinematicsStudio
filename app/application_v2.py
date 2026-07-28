import sys
import traceback

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from ui_v2.branding import BrandAssetLoader, BrandSplashScreen
from ui_v2.main_window import MainWindow
from ui_v2.theme import THEMES


def run():
    """Start the V2 desktop application with production-safe defaults."""

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    brand_loader = BrandAssetLoader()
    app.setOrganizationName(brand_loader.config.company)
    app.setApplicationName(brand_loader.config.application_name)
    app.setWindowIcon(brand_loader.load_icon())

    app.setStyleSheet(THEMES.get(brand_loader.config.theme, THEMES["Dark"]))

    sys.excepthook = _show_unhandled_error

    splash = BrandSplashScreen(brand_loader)
    splash.show()
    splash.run_initialization_messages(app)

    try:
        window = MainWindow(brand_loader=brand_loader)
    except Exception:
        _show_startup_error()
        raise

    window.showMaximized()
    splash.finish(window)

    app.exec()


def _show_startup_error():
    """Display a concise startup failure message before re-raising."""

    QMessageBox.critical(
        None,
        "Kinematics Studio Startup Error",
        "Kinematics Studio could not start. Review the console log for details.",
    )


def _show_unhandled_error(exc_type, exc_value, exc_traceback):
    """Show unexpected runtime errors without hiding diagnostic console output."""

    message = "".join(
        traceback.format_exception_only(exc_type, exc_value)
    ).strip()

    QMessageBox.critical(
        None,
        "Kinematics Studio Error",
        f"An unexpected error occurred:\n\n{message}",
    )

    sys.__excepthook__(exc_type, exc_value, exc_traceback)

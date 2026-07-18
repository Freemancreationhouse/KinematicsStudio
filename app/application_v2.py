import sys
import traceback

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from ui_v2.main_window import MainWindow
from ui_v2.theme import DARK_THEME


def run():
    """Start the V2 desktop application with production-safe defaults."""

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setOrganizationName("Kinematics Studio")
    app.setApplicationName("Kinematics Studio V2")

    app.setStyleSheet(DARK_THEME)

    sys.excepthook = _show_unhandled_error

    try:
        window = MainWindow()
    except Exception:
        _show_startup_error()
        raise

    window.showMaximized()

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

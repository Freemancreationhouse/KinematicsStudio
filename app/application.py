import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.styles import DARK_THEME


def run():

    app = QApplication(sys.argv)

    app.setStyleSheet(DARK_THEME)

    window = MainWindow()

    window.show()

    app.exec()
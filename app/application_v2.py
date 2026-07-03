import sys

from PySide6.QtWidgets import QApplication

from ui_v2.main_window import MainWindow
from ui_v2.theme import DARK_THEME


def run():

    app = QApplication(sys.argv)

    app.setStyleSheet(DARK_THEME)

    window = MainWindow()

    window.showMaximized()

    app.exec()
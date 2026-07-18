import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from ui_v2.main_window import MainWindow


qt_app = QApplication.instance() or QApplication([])

window = MainWindow()

assert window.bcf_dock.objectName() == "BCFTopicBrowserDock"
assert window.bcf_panel.workspace is window.canvas.app.workspace

project_tab = window.ribbon.tabs.widget(0)
button_texts = [
    project_tab.layout().itemAt(index).widget().text()
    for index in range(project_tab.layout().count())
    if project_tab.layout().itemAt(index).widget() is not None
]

assert "Import CAD" in button_texts
assert "Export CAD" in button_texts
assert "Validate Exchange" in button_texts

window._commands_changed(window.canvas.app.workspace.command_manager)
window._bcf_changed()

print("3d-bcf-exchange-main-window-ok")

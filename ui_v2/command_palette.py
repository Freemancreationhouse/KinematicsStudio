from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)


class CommandPalette(QDialog):
    """Keyboard-first command, tool, workspace, settings and documentation search."""

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle("Command Palette")
        self.setModal(False)
        self.resize(560, 420)
        self.actions = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search commands, tools, workspaces, settings, documentation...")
        self.results = QListWidget()
        layout.addWidget(self.search)
        layout.addWidget(self.results, 1)

        self.search.textChanged.connect(self.refresh)
        self.results.itemActivated.connect(self.activate_item)
        self.refresh()

    def rebuild_actions(self):
        """Collect searchable actions from existing production UI systems."""

        actions = []
        tool_manager = self.main_window.canvas.app.tool_manager
        for name in sorted(tool_manager.tools):
            label = name[:-4] if name.endswith("Tool") else name
            actions.append(
                {
                    "label": label,
                    "category": "Tool",
                    "callback": lambda tool=name: tool_manager.activate(tool),
                }
            )

        for index in range(self.main_window.ribbon.tabs.count()):
            tab = self.main_window.ribbon.tabs.widget(index)
            tab_name = self.main_window.ribbon.tabs.tabText(index)
            for button in tab.findChildren(QPushButton):
                if button.isVisibleTo(tab):
                    actions.append(
                        {
                            "label": f"{tab_name}: {button.text()}",
                            "category": "Command",
                            "callback": button.click,
                        }
                    )

        workspace_actions = [
            ("2D View", self.main_window.show_2d_view),
            ("3D View", self.main_window.show_3d_view),
            ("Focus Mode", self.main_window.enter_focus_mode),
            ("Presentation Mode", self.main_window.enter_presentation_mode),
            ("Reset Workspace Layout", self.main_window.reset_workspace_layout),
        ]
        for label, callback in workspace_actions:
            actions.append({"label": label, "category": "Workspace", "callback": callback})

        documentation_actions = [
            ("Open ROADMAP.md", "Documentation"),
            ("Open TASKS.md", "Documentation"),
            ("Open SPECIFICATIONS.md", "Documentation"),
            ("Open CHANGELOG.md", "Documentation"),
        ]
        for label, category in documentation_actions:
            actions.append({"label": label, "category": category, "callback": lambda: None})

        actions.append({"label": "Theme: Dark", "category": "Settings", "callback": lambda: self.main_window.apply_theme("Dark")})
        actions.append({"label": "Theme: Light", "category": "Settings", "callback": lambda: self.main_window.apply_theme("Light")})
        actions.append({"label": "Theme: High Contrast", "category": "Settings", "callback": lambda: self.main_window.apply_theme("High Contrast")})
        self.actions = actions

    def refresh(self):
        """Refresh filtered command results."""

        if not self.actions:
            self.rebuild_actions()
        query = self.search.text().strip().lower()
        self.results.clear()
        for action in self.actions:
            haystack = f"{action['category']} {action['label']}".lower()
            if query and query not in haystack:
                continue
            item = QListWidgetItem(f"{action['category']}  ·  {action['label']}")
            item.setData(Qt.UserRole, action)
            self.results.addItem(item)
        if self.results.count():
            self.results.setCurrentRow(0)

    def activate_item(self, item=None):
        """Execute the selected palette action."""

        item = item or self.results.currentItem()
        if item is None:
            return
        action = item.data(Qt.UserRole)
        callback = action.get("callback")
        if callback:
            callback()
        self.close()

    def keyPressEvent(self, event):
        """Support Enter and Escape keyboard-first palette navigation."""

        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.activate_item()
            return
        if event.key() == Qt.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

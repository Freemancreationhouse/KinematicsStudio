from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
)


class ExplorerPanel(QWidget):
    """Displays project structure and command history."""

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel("Explorer")

        layout.addWidget(title)

        self.tree = QTreeWidget()

        self.tree.setHeaderHidden(True)

        layout.addWidget(self.tree)
        self.history = None
        self._history_count = 0

        self.build()

    # ---------------------------------------------

    def build(self):

        project = QTreeWidgetItem(["Project"])

        layers = QTreeWidgetItem(["Layers"])

        assets = QTreeWidgetItem(["Assets"])

        history = QTreeWidgetItem(["History"])
        self.history = history

        project.addChild(layers)

        project.addChild(assets)

        project.addChild(history)

        self.tree.addTopLevelItem(project)

        project.setExpanded(True)
        history.setExpanded(True)

    # ---------------------------------------------

    def show_history(self, command_manager):

        if self.history is None:
            return

        commands = command_manager.history()

        if len(commands) == self._history_count + 1:
            self.history.addChild(
                QTreeWidgetItem([
                    f"{len(commands)}. {commands[-1].name}"
                ])
            )
            self._history_count = len(commands)
            self.history.setExpanded(True)
            return

        if len(commands) < self._history_count:
            while self.history.childCount() > len(commands):
                self.history.takeChild(self.history.childCount() - 1)
            self._history_count = len(commands)
            self.history.setExpanded(True)
            return

        if len(commands) == self._history_count:
            return

        self.history.takeChildren()

        for index, command in enumerate(commands, 1):
            self.history.addChild(
                QTreeWidgetItem([f"{index}. {command.name}"])
            )

        self._history_count = len(commands)
        self.history.setExpanded(True)

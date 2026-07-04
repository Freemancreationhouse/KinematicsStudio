from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
)


class ExplorerPanel(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel("Explorer")

        layout.addWidget(title)

        self.tree = QTreeWidget()

        self.tree.setHeaderHidden(True)

        layout.addWidget(self.tree)
        self.history = None

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

        self.history.takeChildren()

        for index, command in enumerate(command_manager.history(), 1):
            self.history.addChild(
                QTreeWidgetItem([f"{index}. {command.name}"])
            )

        self.history.setExpanded(True)

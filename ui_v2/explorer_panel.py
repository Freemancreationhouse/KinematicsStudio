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

        self.build()

    # ---------------------------------------------

    def build(self):

        project = QTreeWidgetItem(["Project"])

        layers = QTreeWidgetItem(["Layers"])

        assets = QTreeWidgetItem(["Assets"])

        history = QTreeWidgetItem(["History"])

        project.addChild(layers)

        project.addChild(assets)

        project.addChild(history)

        self.tree.addTopLevelItem(project)

        project.setExpanded(True)
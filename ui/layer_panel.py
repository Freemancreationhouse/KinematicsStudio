from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QPushButton,
    QHBoxLayout,
    QInputDialog,
)


class LayerPanel(QWidget):

    def __init__(self, project):
        super().__init__()

        self.project = project

        layout = QVBoxLayout(self)

        self.list = QListWidget()

        layout.addWidget(self.list)

        buttons = QHBoxLayout()

        btn_add = QPushButton("+")
        btn_delete = QPushButton("-")
        btn_current = QPushButton("Current")

        buttons.addWidget(btn_add)
        buttons.addWidget(btn_delete)
        buttons.addWidget(btn_current)

        layout.addLayout(buttons)

        btn_add.clicked.connect(self.add_layer)
        btn_delete.clicked.connect(self.delete_layer)
        btn_current.clicked.connect(self.make_current)

        self.refresh()

    # ----------------------------------------

    def refresh(self):

        self.list.clear()

        for name in self.project.layer_manager.names():

            layer = self.project.layer_manager.get(name)

            text = name

            if layer == self.project.layer_manager.current:
                text += "   ★"

            self.list.addItem(text)

    # ----------------------------------------

    def add_layer(self):

        name, ok = QInputDialog.getText(
            self,
            "New Layer",
            "Layer Name"
        )

        if ok and name:

            self.project.layer_manager.add(name)

            self.refresh()

    # ----------------------------------------

    def delete_layer(self):

        item = self.list.currentItem()

        if item is None:
            return

        name = item.text().replace("   ★", "")

        self.project.layer_manager.remove(name)

        self.refresh()

    # ----------------------------------------

    def make_current(self):

        item = self.list.currentItem()

        if item is None:
            return

        name = item.text().replace("   ★", "")

        self.project.layer_manager.set_current(name)

        self.refresh()
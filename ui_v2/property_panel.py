import math

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLineEdit,
    QWidget,
)

from engine.commands import UpdateEntityCommand, UpdateLayerCommand
from engine.geometry import Vector2


class LayerComboBox(QComboBox):
    """Combo box with QLineEdit-like text helpers for legacy tests."""

    def text(self):

        return self.currentText()

    # -----------------------------------------

    def setText(self, value):

        index = self.findText(value)

        if index >= 0:
            self.setCurrentIndex(index)


class PropertyPanel(QWidget):
    """Displays and edits selected entity properties through commands."""

    def __init__(self):

        super().__init__()

        self.workspace = None
        self.on_change = None
        self.selected = []
        self._loading = False

        layout = QFormLayout(self)

        self.type = self._read_only_field()
        self.layer = LayerComboBox()
        self.visible = QCheckBox()
        self.locked = QCheckBox()

        self.x = QLineEdit()
        self.y = QLineEdit()
        self.x2 = QLineEdit()
        self.y2 = QLineEdit()
        self.length = QLineEdit()
        self.angle = QLineEdit()
        self.width = QLineEdit()
        self.height = QLineEdit()
        self.radius = QLineEdit()
        self.diameter = QLineEdit()

        self.color = QLineEdit()
        self.line_type = QLineEdit()
        self.line_weight = QLineEdit()

        self._add_rows(layout)
        self._wire_signals()
        self.clear()

    # -----------------------------------------

    def set_workspace(self, workspace, on_change=None):
        """Attach the workspace used for command-driven property edits."""

        self.workspace = workspace
        self.on_change = on_change
        self._populate_layers()

    # -----------------------------------------

    def clear(self):
        """Clear all displayed values."""

        self._loading = True
        self.selected = []
        self.type.setText("None")

        for field in self._text_fields():
            field.clear()
            field.setEnabled(False)

        self.layer.clear()
        self.layer.setEnabled(False)
        self.visible.setChecked(False)
        self.visible.setEnabled(False)
        self.locked.setChecked(False)
        self.locked.setEnabled(False)
        self._loading = False

    # -----------------------------------------

    def show_selection(self, selected):
        """Display editable properties for the current selection."""

        self._loading = True
        self.selected = list(selected or [])

        if not self.selected:
            self._loading = False
            self.clear()
            return

        self._set_enabled(len(self.selected) == 1)

        if len(self.selected) > 1:
            self._show_multiple()
        else:
            self._show_entity(self.selected[0])

        self._loading = False

    # -----------------------------------------

    def _add_rows(self, layout):

        layout.addRow("Entity Type", self.type)
        layout.addRow("Layer", self.layer)
        layout.addRow("Visibility", self.visible)
        layout.addRow("Lock State", self.locked)
        layout.addRow("Start / Center X", self.x)
        layout.addRow("Start / Center Y", self.y)
        layout.addRow("End X", self.x2)
        layout.addRow("End Y", self.y2)
        layout.addRow("Length", self.length)
        layout.addRow("Angle", self.angle)
        layout.addRow("Width", self.width)
        layout.addRow("Height", self.height)
        layout.addRow("Radius", self.radius)
        layout.addRow("Diameter", self.diameter)
        layout.addRow("Layer Color", self.color)
        layout.addRow("Line Type", self.line_type)
        layout.addRow("Line Weight", self.line_weight)

    # -----------------------------------------

    def _wire_signals(self):

        self.layer.currentTextChanged.connect(self._layer_changed)
        self.visible.stateChanged.connect(self._visible_changed)
        self.locked.stateChanged.connect(self._locked_changed)

        self.x.editingFinished.connect(lambda: self._geometry_changed("x"))
        self.y.editingFinished.connect(lambda: self._geometry_changed("y"))
        self.x2.editingFinished.connect(lambda: self._geometry_changed("x2"))
        self.y2.editingFinished.connect(lambda: self._geometry_changed("y2"))
        self.length.editingFinished.connect(lambda: self._geometry_changed("length"))
        self.angle.editingFinished.connect(lambda: self._geometry_changed("angle"))
        self.width.editingFinished.connect(lambda: self._geometry_changed("width"))
        self.height.editingFinished.connect(lambda: self._geometry_changed("height"))
        self.radius.editingFinished.connect(lambda: self._geometry_changed("radius"))
        self.diameter.editingFinished.connect(lambda: self._geometry_changed("diameter"))

        self.color.editingFinished.connect(lambda: self._layer_property_changed("color"))
        self.line_type.editingFinished.connect(
            lambda: self._layer_property_changed("line_type")
        )
        self.line_weight.editingFinished.connect(
            lambda: self._layer_property_changed("line_weight")
        )

    # -----------------------------------------

    def _show_multiple(self):

        self._clear_text_values()
        self.type.setText(f"Multiple ({len(self.selected)})")
        self.layer.setEnabled(False)
        self.visible.setEnabled(False)
        self.locked.setEnabled(False)

    # -----------------------------------------

    def _show_entity(self, entity):

        self._clear_text_values()
        self.type.setText(entity.type_name)
        self.visible.setChecked(getattr(entity, "visible", True))
        self.locked.setChecked(getattr(entity, "locked", False))
        self._populate_layers(getattr(entity, "layer_name", ""))
        self._show_layer_name(getattr(entity, "layer_name", ""))
        self._show_layer_properties(entity)

        if hasattr(entity, "start") and hasattr(entity, "end"):
            self._show_line(entity)
        elif hasattr(entity, "p1") and hasattr(entity, "p2"):
            self._show_rectangle(entity)
        elif hasattr(entity, "center") and hasattr(entity, "radius"):
            self._show_circle(entity)

    # -----------------------------------------

    def _show_line(self, entity):

        self._set_point_pair(entity.start, entity.end)
        dx = entity.end.x - entity.start.x
        dy = entity.end.y - entity.start.y
        self.length.setText(self._number(math.hypot(dx, dy)))
        self.angle.setText(self._number(math.degrees(math.atan2(dy, dx))))

    # -----------------------------------------

    def _show_rectangle(self, entity):

        self._set_point_pair(entity.p1, entity.p2)
        self.width.setText(self._number(entity.width))
        self.height.setText(self._number(entity.height))

    # -----------------------------------------

    def _show_circle(self, entity):

        self.x.setText(self._number(entity.center.x))
        self.y.setText(self._number(entity.center.y))
        self.radius.setText(self._number(entity.radius))
        self.diameter.setText(self._number(entity.radius * 2.0))

    # -----------------------------------------

    def _show_layer_properties(self, entity):

        layer = self._entity_layer(entity)

        if layer is None:
            self.color.setText(getattr(entity, "display_color", ""))
            return

        self.color.setText(layer.color)
        self.line_type.setText(layer.line_type)
        self.line_weight.setText(self._number(layer.line_weight))

    # -----------------------------------------

    def _layer_changed(self, name):

        if self._ignore_edit() or not name:
            return

        entity = self.selected[0]
        layer = self.workspace.layer_manager.get(name)

        if layer is None or layer is self._entity_layer(entity):
            return

        self._execute_entity_update(entity, {"layer_id": layer.id})

    # -----------------------------------------

    def _visible_changed(self, state):

        if self._ignore_edit():
            return

        self._execute_entity_update(self.selected[0], {"visible": bool(state)})

    # -----------------------------------------

    def _locked_changed(self, state):

        if self._ignore_edit():
            return

        self._execute_entity_update(self.selected[0], {"locked": bool(state)})

    # -----------------------------------------

    def _geometry_changed(self, field):

        if self._ignore_edit():
            return

        entity = self.selected[0]
        state = self._edited_geometry_state(entity, field)

        if state:
            self._execute_entity_update(entity, state)

    # -----------------------------------------

    def _layer_property_changed(self, key):

        if self._ignore_edit():
            return

        layer = self._entity_layer(self.selected[0])

        if layer is None:
            return

        before = self._layer_state(layer)
        after = dict(before)

        if key == "color":
            after["color"] = self.color.text().strip() or layer.color
        elif key == "line_type":
            after["line_type"] = self.line_type.text().strip() or layer.line_type
        elif key == "line_weight":
            value = self._float(self.line_weight)

            if value is None:
                self.show_selection(self.selected)
                return

            after["line_weight"] = max(0.0, value)

        if after == before:
            return

        command = UpdateLayerCommand(self.workspace, layer, before, after)
        self.workspace.command_manager.execute(command)
        self._changed()

    # -----------------------------------------

    def _edited_geometry_state(self, entity, field):

        if hasattr(entity, "start") and hasattr(entity, "end"):
            return self._line_state(entity, field)

        if hasattr(entity, "p1") and hasattr(entity, "p2"):
            return self._rectangle_state(entity, field)

        if hasattr(entity, "center") and hasattr(entity, "radius"):
            return self._circle_state(entity, field)

        return {}

    # -----------------------------------------

    def _line_state(self, entity, field):

        start = entity.start.copy()
        end = entity.end.copy()

        if field == "x":
            start.x = self._float(self.x, start.x)
        elif field == "y":
            start.y = self._float(self.y, start.y)
        elif field == "x2":
            end.x = self._float(self.x2, end.x)
        elif field == "y2":
            end.y = self._float(self.y2, end.y)
        elif field in ("length", "angle"):
            end = self._line_end_from_polar(start, end, field)
        else:
            return {}

        return {"start": start, "end": end}

    # -----------------------------------------

    def _rectangle_state(self, entity, field):

        p1 = entity.p1.copy()
        p2 = entity.p2.copy()

        if field == "x":
            p1.x = self._float(self.x, p1.x)
        elif field == "y":
            p1.y = self._float(self.y, p1.y)
        elif field == "x2":
            p2.x = self._float(self.x2, p2.x)
        elif field == "y2":
            p2.y = self._float(self.y2, p2.y)
        elif field == "width":
            p2.x = p1.x + self._signed_size(self.width, p1.x, p2.x)
        elif field == "height":
            p2.y = p1.y + self._signed_size(self.height, p1.y, p2.y)
        else:
            return {}

        return {"p1": p1, "p2": p2}

    # -----------------------------------------

    def _circle_state(self, entity, field):

        center = entity.center.copy()
        radius = entity.radius

        if field == "x":
            center.x = self._float(self.x, center.x)
        elif field == "y":
            center.y = self._float(self.y, center.y)
        elif field == "radius":
            radius = max(0.0, self._float(self.radius, radius))
        elif field == "diameter":
            radius = max(0.0, self._float(self.diameter, radius * 2.0) / 2.0)
        else:
            return {}

        return {"center": center, "radius": radius}

    # -----------------------------------------

    def _execute_entity_update(self, entity, after_values):

        before = self._entity_state(entity, after_values)
        after = dict(before)
        after.update(after_values)

        if after == before:
            self.show_selection(self.selected)
            return

        command = UpdateEntityCommand(
            entity,
            workspace=self.workspace,
            before=before,
            after=after,
        )
        self.workspace.command_manager.execute(command)
        self._changed()

    # -----------------------------------------

    def _entity_state(self, entity, fields):

        state = {}

        for key in fields:
            state[key] = getattr(entity, key, None)

        if "layer_id" in fields:
            state["layer_id"] = getattr(entity, "layer_id", None)

        return state

    # -----------------------------------------

    def _layer_state(self, layer):

        return {
            "visible": layer.visible,
            "locked": layer.locked,
            "color": layer.color,
            "line_type": layer.line_type,
            "line_weight": layer.line_weight,
        }

    # -----------------------------------------

    def _populate_layers(self, current=""):

        if self.workspace is None:
            return

        previous = self._loading
        self._loading = True
        self.layer.clear()

        for name in self.workspace.layer_manager.names():
            self.layer.addItem(name)

        if current:
            index = self.layer.findText(current)

            if index >= 0:
                self.layer.setCurrentIndex(index)

        self._loading = previous

    # -----------------------------------------

    def _show_layer_name(self, name):

        if self.workspace is not None or not name:
            return

        self.layer.clear()
        self.layer.addItem(name)
        self.layer.setCurrentIndex(0)

    # -----------------------------------------

    def _entity_layer(self, entity):

        if self.workspace is not None:
            return self.workspace.entity_layer(entity)

        return getattr(entity, "layer", None)

    # -----------------------------------------

    def _set_point_pair(self, p1, p2):

        self.x.setText(self._number(p1.x))
        self.y.setText(self._number(p1.y))
        self.x2.setText(self._number(p2.x))
        self.y2.setText(self._number(p2.y))

    # -----------------------------------------

    def _line_end_from_polar(self, start, end, field):

        dx = end.x - start.x
        dy = end.y - start.y
        length = math.hypot(dx, dy)
        angle = math.degrees(math.atan2(dy, dx))

        if field == "length":
            length = max(0.0, self._float(self.length, length))
        else:
            angle = self._float(self.angle, angle)

        radians = math.radians(angle)

        return Vector2(
            start.x + math.cos(radians) * length,
            start.y + math.sin(radians) * length,
        )

    # -----------------------------------------

    def _signed_size(self, field, start, end):

        value = abs(self._float(field, abs(end - start)))
        direction = -1.0 if end < start else 1.0

        return value * direction

    # -----------------------------------------

    def _ignore_edit(self):

        return self._loading or self.workspace is None or len(self.selected) != 1

    # -----------------------------------------

    def _changed(self):

        if self.on_change:
            self.on_change()
        else:
            self.show_selection(self.selected)

    # -----------------------------------------

    def _set_enabled(self, enabled):

        for field in self._text_fields():
            field.setEnabled(enabled)

        self.layer.setEnabled(enabled)
        self.visible.setEnabled(enabled)
        self.locked.setEnabled(enabled)

    # -----------------------------------------

    def _clear_text_values(self):

        for field in self._text_fields():
            field.clear()

    # -----------------------------------------

    def _text_fields(self):

        return [
            self.x,
            self.y,
            self.x2,
            self.y2,
            self.length,
            self.angle,
            self.width,
            self.height,
            self.radius,
            self.diameter,
            self.color,
            self.line_type,
            self.line_weight,
        ]

    # -----------------------------------------

    def _read_only_field(self):

        field = QLineEdit()
        field.setReadOnly(True)

        return field

    # -----------------------------------------

    def _float(self, field, fallback=None):

        try:
            return float(field.text())
        except ValueError:
            if fallback is not None:
                return fallback

            return None

    # -----------------------------------------

    def _number(self, value):

        return f"{value:.2f}"

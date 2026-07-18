from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF

from engine.geometry import Vector3


class Renderer3D:
    """Read-only 3D renderer for grids, axes and future scene traversal."""

    def __init__(self):

        self.camera = None
        self.grid_size = 50
        self.grid_lines = 20
        self.debug_bounds = False

    # --------------------------------

    def render(self, painter, workspace, width, height):
        """Render the current 3D foundation scene."""

        if self.camera is None:
            return

        self.camera.resize(width, height)
        style = self._visual_style(workspace)
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(0, 0, width, height, QColor(getattr(style, "background", "#16191d")))

        if getattr(style, "grid_visible", True):
            self._draw_grid(painter, workspace)

        if getattr(style, "axis_visible", True):
            self._draw_axes(painter, workspace)

        self._draw_origin(painter)
        self._draw_scene(painter, workspace)
        painter.restore()

    # --------------------------------

    def _draw_grid(self, painter, workspace):

        minor_pen = QPen(QColor(52, 58, 64), 1)
        major_pen = QPen(QColor(78, 86, 95), 1)
        minor_pen.setCosmetic(True)
        major_pen.setCosmetic(True)

        coordinate_manager = getattr(workspace, "coordinate_system_manager", None)

        if coordinate_manager is not None and not coordinate_manager.grid_visible:
            return

        active = getattr(coordinate_manager, "active", None)
        span = self.grid_lines
        size = (
            getattr(coordinate_manager, "grid_spacing", self.grid_size)
            if coordinate_manager is not None else self.grid_size
        )
        subdivisions = max(
            getattr(coordinate_manager, "grid_subdivisions", 5)
            if coordinate_manager is not None else 5,
            1,
        )
        minor_size = size / subdivisions

        for index in range(-span * subdivisions, span * subdivisions + 1):
            painter.setPen(major_pen if index % 5 == 0 else minor_pen)
            value = index * minor_size
            self._draw_line(painter, self._ucs_point(active, -span * size, value, 0.0), self._ucs_point(active, span * size, value, 0.0))
            self._draw_line(painter, self._ucs_point(active, value, -span * size, 0.0), self._ucs_point(active, value, span * size, 0.0))

    # --------------------------------

    def _draw_axes(self, painter, workspace):

        coordinate_manager = getattr(workspace, "coordinate_system_manager", None)
        active = getattr(coordinate_manager, "active", None)
        origin = getattr(active, "origin", Vector3())
        x_axis = getattr(active, "x_axis", Vector3(1.0, 0.0, 0.0))
        y_axis = getattr(active, "y_axis", Vector3(0.0, 1.0, 0.0))
        z_axis = getattr(active, "z_axis", Vector3(0.0, 0.0, 1.0))

        axes = [
            (origin, origin + x_axis * 400.0, QColor("#ef5350"), "X"),
            (origin, origin + y_axis * 400.0, QColor("#66bb6a"), "Y"),
            (origin, origin + z_axis * 400.0, QColor("#42a5f5"), "Z"),
        ]

        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)

        for start, end, color, label in axes:
            pen = QPen(color, 2)
            pen.setCosmetic(True)
            painter.setPen(pen)
            self._draw_line(painter, start, end)
            screen = self.camera.project(end)

            if screen is not None:
                painter.drawText(QPointF(screen[0] + 6, screen[1] - 6), label)

    # --------------------------------

    def _draw_origin(self, painter):

        screen = self.camera.project(Vector3())

        if screen is None:
            return

        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.setBrush(QColor(255, 255, 255, 160))
        painter.drawEllipse(QPointF(screen[0], screen[1]), 4, 4)

    # --------------------------------

    def _draw_scene(self, painter, workspace):
        """Traverse the workspace once for future 3D scene adapters."""

        entities = (
            workspace.visible_3d_entities()
            if hasattr(workspace, "visible_3d_entities")
            else []
        )

        for entity in entities:
            self._draw_entity(painter, workspace, entity)

            if self.debug_bounds:
                self._draw_bounds(painter, entity.bounding_box3d)

        self._draw_sections(painter, workspace)
        self._draw_analysis_overlays(painter, workspace, entities)
        self._draw_measurements(painter, workspace)
        self._draw_annotations(painter, workspace)
        self._draw_references(painter, workspace)
        self._draw_clashes(painter, workspace)
        self._draw_bcf_topics(painter, workspace)
        self._draw_issues(painter, workspace)
        self._draw_review_overlays(painter, workspace)
        self._draw_session_overlay(painter, workspace)
        self._draw_exchange_validation(painter, workspace)
        self._draw_compare_results(painter, workspace)
        self._draw_revisions(painter, workspace)
        self._draw_coordination_packages(painter, workspace)
        self._draw_bim(painter, workspace)
        self._draw_products(painter, workspace)
        count = len(entities)
        painter.setPen(QColor("#b0bec5"))
        painter.drawText(QPointF(12, 24), f"3D Scene Entities: {count}")
        self._draw_snap_preview(painter, workspace)
        self._draw_gizmo(painter, workspace)

    # --------------------------------

    def _draw_entity(self, painter, workspace, entity):

        color = QColor(getattr(entity, "display_color", "#FFFFFF"))
        style = self._visual_style(workspace)

        if getattr(entity, "selected", False):
            color = QColor(getattr(style, "selection_color", "#ffeb3b"))
        elif getattr(entity, "hovered", False):
            color = QColor(getattr(style, "hover_color", "#80deea"))
        elif self._is_snap_highlight(workspace, entity):
            color = QColor(getattr(style, "snap_color", "#ffab40"))

        if getattr(entity, "type_name", "") == "MeshEntity":
            self._draw_mesh(painter, workspace, entity, color)
            return

        pen = QPen(color, 3 if getattr(entity, "selected", False) else 1)
        pen.setCosmetic(True)
        painter.setPen(pen)

        for start, end in entity.segments():
            self._draw_line(painter, start, end)

        for point in entity.points():
            self._draw_point(painter, point, color)

    # --------------------------------

    def _draw_mesh(self, painter, workspace, entity, color):

        mode = self._display_mode(workspace, entity)
        style = self._visual_style(workspace)

        if mode == "bounding_box":
            self._draw_bounds(painter, entity.bounding_box3d)
            return

        if mode in ("shaded", "shaded_with_edges", "x_ray", "analysis_overlay") and getattr(style, "face_visible", True):
            self._draw_mesh_faces(painter, entity, color, mode)

        pen = QPen(color, 3 if getattr(entity, "selected", False) else 1)
        pen.setCosmetic(True)
        painter.setPen(pen)

        if (
            mode in ("wireframe", "hidden_line", "shaded_with_edges", "x_ray", "analysis_overlay") and
            getattr(style, "edge_visible", True)
        ):
            for start, end in entity.segments():
                self._draw_line(painter, start, end)

    # --------------------------------

    def _draw_mesh_faces(self, painter, entity, color, mode="shaded"):

        fill = QColor(color)
        fill.setAlpha(34 if mode == "x_ray" else 80)
        painter.setBrush(fill)
        painter.setPen(QPen(QColor(fill), 1))

        for triangle in entity.triangles():
            polygon = QPolygonF()

            for point in triangle:
                screen = self.camera.project(point)

                if screen is None:
                    polygon = None
                    break

                polygon.append(QPointF(screen[0], screen[1]))

            if polygon is not None:
                painter.drawPolygon(polygon)

    # --------------------------------

    def _draw_point(self, painter, point, color):

        screen = self.camera.project(point)

        if screen is None:
            return

        painter.setBrush(color)
        painter.drawEllipse(QPointF(screen[0], screen[1]), 4, 4)

    # --------------------------------

    def _draw_bounds(self, painter, box):

        corners = box.corners()

        if not corners:
            return

        pen = QPen(QColor("#9e9e9e"), 1)
        pen.setCosmetic(True)
        painter.setPen(pen)
        edges = [
            (0, 1), (0, 2), (0, 4), (3, 1),
            (3, 2), (3, 7), (5, 1), (5, 4),
            (5, 7), (6, 2), (6, 4), (6, 7),
        ]

        for start, end in edges:
            self._draw_line(painter, corners[start], corners[end])

    # --------------------------------

    def _draw_gizmo(self, painter, workspace):

        gizmo = getattr(workspace, "transform_gizmo", None)

        if gizmo is None or not gizmo.visible:
            return

        selected = [
            entity for entity in getattr(workspace.selection, "selected", [])
            if getattr(entity, "is_3d", False)
        ]

        if not selected:
            return

        origin = gizmo.origin_for_selection(selected)
        self._draw_gizmo_pivot(painter, gizmo, origin)
        colors = {
            "X": QColor("#ef5350"),
            "Y": QColor("#66bb6a"),
            "Z": QColor("#42a5f5"),
        }

        for axis, (start, end) in gizmo.axis_segments(origin).items():
            color = QColor("#ffeb3b") if gizmo.highlighted_axis == axis else colors[axis]
            pen = QPen(color, 4 if gizmo.highlighted_axis == axis else 2)
            pen.setCosmetic(True)
            painter.setPen(pen)
            self._draw_line(painter, start, end)
            screen = self.camera.project(end)

            if screen is not None:
                painter.drawText(QPointF(screen[0] + 4, screen[1] - 4), f"{gizmo.mode[:1].upper()}{axis}")

        label_screen = self.camera.project(origin)

        if label_screen is not None:
            constraint = gizmo.axis_constraint or gizmo.plane_constraint or "free"
            painter.setPen(QColor("#eceff1"))
            painter.drawText(
                QPointF(label_screen[0] + 8, label_screen[1] + 18),
                f"{gizmo.coordinate_mode} | {gizmo.pivot_mode} | {constraint}",
            )

    # --------------------------------

    def _draw_gizmo_pivot(self, painter, gizmo, origin):

        screen = self.camera.project(origin)

        if screen is None:
            return

        pen = QPen(QColor("#ffab40"), 2)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(QColor(255, 171, 64, 120))
        painter.drawEllipse(QPointF(screen[0], screen[1]), 6, 6)

    # --------------------------------

    def _draw_snap_preview(self, painter, workspace):

        snap_manager = getattr(workspace, "snap_manager3d", None)

        if snap_manager is None or snap_manager.active_snap is None:
            return

        result = snap_manager.active_snap
        screen = self.camera.project(result.point)

        if screen is None:
            return

        color = QColor("#ffab40")
        pen = QPen(color, 2)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(QColor(255, 171, 64, 90))
        center = QPointF(screen[0], screen[1])
        painter.drawEllipse(center, 7, 7)
        painter.drawLine(QPointF(screen[0] - 10, screen[1]), QPointF(screen[0] + 10, screen[1]))
        painter.drawLine(QPointF(screen[0], screen[1] - 10), QPointF(screen[0], screen[1] + 10))
        painter.drawText(QPointF(screen[0] + 10, screen[1] - 10), result.mode)

        if result.mode == "AXIS":
            self._draw_line(painter, Vector3(), result.point)

    # --------------------------------

    def _draw_measurements(self, painter, workspace):

        measurements = (
            workspace.visible_measurements()
            if hasattr(workspace, "visible_measurements")
            else []
        )
        manager = getattr(workspace, "measurement_manager", None)
        settings = getattr(manager, "settings", None)

        if not measurements or settings is None:
            return

        pen = QPen(QColor(settings.color), 2)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(QColor(settings.color))

        for measurement in measurements:
            color = QColor("#ffeb3b") if getattr(measurement, "selected", False) else QColor(settings.color)
            pen = QPen(color, 3 if getattr(measurement, "selected", False) else 2)
            pen.setCosmetic(True)
            painter.setPen(pen)

            for start, end in measurement.segments():
                self._draw_line(painter, start, end)

            if settings.show_markers:
                for point in measurement.representative_points():
                    self._draw_point(painter, point, color)

            if settings.show_labels and measurement.points:
                label_point = measurement.points[len(measurement.points) // 2]
                screen = self.camera.project(label_point)

                if screen is not None:
                    painter.drawText(
                        QPointF(screen[0] + 8, screen[1] - 8),
                        measurement.result.label or str(measurement.result.value),
                    )

    # --------------------------------

    def _draw_sections(self, painter, workspace):

        sections = (
            workspace.visible_sections()
            if hasattr(workspace, "visible_sections")
            else []
        )
        manager = getattr(workspace, "section_manager", None)

        if not sections:
            return

        for section in sections:
            color = QColor(getattr(section, "display_color", "#26c6da"))

            if getattr(section, "selected", False):
                color = QColor("#ffeb3b")
            elif manager is not None and manager.active is section:
                color = QColor("#80deea")

            pen = QPen(color, 3 if getattr(section, "selected", False) else 2)
            pen.setCosmetic(True)
            painter.setPen(pen)

            fill = QColor(color)
            fill.setAlpha(28 if getattr(section, "enabled", True) else 10)
            painter.setBrush(fill)
            polygon = QPolygonF()

            for point in section.points():
                screen = self.camera.project(point)

                if screen is None:
                    polygon = None
                    break

                polygon.append(QPointF(screen[0], screen[1]))

            if polygon is not None:
                painter.drawPolygon(polygon)

            painter.setBrush(QColor(color))

            for start, end in section.segments():
                self._draw_line(painter, start, end)

            normal_start, normal_end = section.normal_segment()
            self._draw_line(painter, normal_start, normal_end)
            label = "ON" if getattr(section, "enabled", True) else "OFF"
            screen = self.camera.project(section.origin)

            if screen is not None:
                painter.drawText(QPointF(screen[0] + 8, screen[1] - 8), f"{section.name} [{label}]")

    # --------------------------------

    def _draw_annotations(self, painter, workspace):

        annotations = (
            workspace.visible_annotations3d()
            if hasattr(workspace, "visible_annotations3d")
            else []
        )
        style = self._visual_style(workspace)

        for annotation in annotations:
            color = QColor(getattr(annotation, "display_color", "#ffcc80"))

            if getattr(annotation, "selected", False):
                color = QColor(getattr(style, "selection_color", "#ffeb3b"))

            pen = QPen(color, 3 if getattr(annotation, "selected", False) else 2)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(QColor(color))

            for start, end in annotation.segments():
                self._draw_line(painter, start, end)

            for point in annotation.representative_points():
                self._draw_point(painter, point, color)

            if annotation.points:
                screen = self.camera.project(annotation.points[0])

                if screen is not None:
                    label = annotation.text or annotation.annotation_type
                    painter.drawText(QPointF(screen[0] + 8, screen[1] - 8), label)

    # --------------------------------

    def _draw_review_overlays(self, painter, workspace):

        manager = getattr(workspace, "review_manager", None)

        if manager is None or not manager.visible:
            return

        unresolved = manager.unresolved()

        if not unresolved:
            return

        painter.setPen(QColor("#ff8a65"))
        painter.drawText(QPointF(12, 84), f"Open Reviews: {len(unresolved)}")

    # --------------------------------

    def _draw_references(self, painter, workspace):

        references = (
            workspace.visible_references()
            if hasattr(workspace, "visible_references")
            else []
        )
        style = self._visual_style(workspace)
        manager = getattr(workspace, "reference_manager", None)

        for reference in references:
            model = manager.get_model(reference.model_id) if manager is not None else None
            color = self._reference_color(reference, model)

            if getattr(reference, "selected", False):
                override = getattr(getattr(model, "style_overrides", None), "selection_highlight_override", "")
                color = QColor(override or getattr(style, "selection_color", "#ffeb3b"))
            elif getattr(reference, "hovered", False):
                color = QColor(getattr(style, "hover_color", "#80deea"))

            pen = QPen(color, self._reference_pen_width(reference, model))
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(QColor(color))

            for start, end in self._reference_segments(reference, model):
                self._draw_line(painter, start, end)

            self._draw_point(painter, reference.transform.position, color)
            screen = self.camera.project(reference.transform.position)

            if screen is not None:
                painter.drawText(
                    QPointF(screen[0] + 8, screen[1] - 8),
                    reference.name,
                )

        if manager is not None and manager.isolated_model_ids:
            painter.setPen(QColor("#90caf9"))
            painter.drawText(
                QPointF(12, 124),
                f"Reference Isolation: {len(manager.isolated_model_ids)}",
            )

    # --------------------------------

    def _reference_segments(self, reference, model):

        mesh = getattr(model, "mesh_data", None)

        if mesh is None or not getattr(mesh, "vertices", []):
            return reference.segments()

        return [
            (
                self._transform_reference_point(reference, start),
                self._transform_reference_point(reference, end),
            )
            for start, end in mesh.edge_segments()
        ]

    # --------------------------------

    def _reference_color(self, reference, model):

        style_overrides = getattr(model, "style_overrides", None)
        color = getattr(style_overrides, "display_color", None) or getattr(reference, "display_color", "#90caf9")
        qcolor = QColor(color)
        transparency = max(0.0, min(getattr(style_overrides, "transparency", 0.0), 1.0))
        qcolor.setAlpha(int(255 * (1.0 - transparency)))

        layer_color = self._reference_layer_color(model)

        if layer_color:
            qcolor = QColor(layer_color)
            qcolor.setAlpha(int(255 * (1.0 - transparency)))

        return qcolor

    # --------------------------------

    def _reference_layer_color(self, model):

        if model is None:
            return ""

        visible = model.visible_layer_mappings()

        for mapping in visible:
            if mapping.color_override:
                return mapping.color_override

        return ""

    # --------------------------------

    def _reference_pen_width(self, reference, model):

        style_overrides = getattr(model, "style_overrides", None)

        if getattr(reference, "selected", False):
            return 3

        if style_overrides is not None and (
            style_overrides.wireframe_override or
            style_overrides.hidden_line_override or
            style_overrides.xray_override
        ):
            return 2

        return 1

    # --------------------------------

    def _transform_reference_point(self, reference, point):

        transform = reference.transform
        scale = transform.scale

        return transform.position + Vector3(
            point.x * scale.x,
            point.y * scale.y,
            point.z * scale.z,
        )

    # --------------------------------

    def _draw_clashes(self, painter, workspace):

        clashes = (
            workspace.visible_clashes()
            if hasattr(workspace, "visible_clashes")
            else []
        )
        style = self._visual_style(workspace)
        manager = getattr(workspace, "clash_manager", None)
        current = manager.current_result() if manager is not None else None

        for clash in clashes:
            color = QColor(getattr(clash, "display_color", "#ff5252"))

            if getattr(clash, "selected", False):
                color = QColor(getattr(style, "selection_color", "#ffeb3b"))
            elif current is clash:
                color = QColor("#ffca28")
            elif getattr(clash, "analytics_focus", False):
                color = QColor("#26c6da")
            elif getattr(clash, "linked_issue_id", ""):
                color = QColor("#ff7043")
            elif getattr(clash, "linked_review_id", ""):
                color = QColor("#66bb6a")
            elif getattr(clash, "watch_list", False):
                color = QColor("#ab47bc")
            elif getattr(clash, "review_queue", False):
                color = QColor("#42a5f5")
            elif getattr(clash, "hovered", False):
                color = QColor(getattr(style, "hover_color", "#80deea"))

            pen = QPen(color, 3 if getattr(clash, "selected", False) or current is clash else 2)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(QColor(color))

            for start, end in clash.segments():
                self._draw_line(painter, start, end)

            if getattr(clash, "bounding_box3d", None).valid:
                self._draw_bounds(painter, clash.bounding_box3d)

            screen = self.camera.project(clash.location)

            if screen is not None:
                painter.drawText(
                    QPointF(screen[0] + 8, screen[1] - 8),
                    f"{clash.clash_type} [{clash.status}]",
                )

        if manager is not None and clashes:
            painter.setPen(QColor("#ff8a80"))
            painter.drawText(QPointF(12, 144), f"Clashes: {len(clashes)}")

    # --------------------------------

    def _draw_bcf_topics(self, painter, workspace):

        topics = (
            workspace.visible_bcf_topics()
            if hasattr(workspace, "visible_bcf_topics")
            else []
        )
        style = self._visual_style(workspace)

        for topic in topics:
            color = QColor(getattr(topic, "display_color", "#29b6f6"))

            if getattr(topic, "selected", False):
                color = QColor(getattr(style, "selection_color", "#ffeb3b"))
            elif getattr(topic, "linked_clash_id", ""):
                color = QColor("#ff7043")
            elif getattr(topic, "linked_issue_id", ""):
                color = QColor("#42a5f5")
            elif getattr(topic, "linked_review_id", ""):
                color = QColor("#66bb6a")

            pen = QPen(color, 3 if getattr(topic, "selected", False) else 2)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(QColor(color))

            for start, end in topic.segments():
                self._draw_line(painter, start, end)

            screen = self.camera.project(topic.location)

            if screen is not None:
                painter.drawEllipse(QPointF(screen[0], screen[1]), 5, 5)
                painter.drawText(
                    QPointF(screen[0] + 8, screen[1] - 8),
                    f"BCF: {topic.title} [{topic.status}]",
                )

        if topics:
            painter.setPen(QColor("#29b6f6"))
            painter.drawText(QPointF(12, 164), f"BCF Topics: {len(topics)}")

    # --------------------------------

    def _draw_exchange_validation(self, painter, workspace):

        manager = getattr(getattr(workspace, "import_manager", None), "validation_manager", None)

        if manager is None or not manager.settings.get("highlight_issues", True):
            return

        highlighted = manager.highlight_entities(workspace)

        if not highlighted:
            return

        pen = QPen(QColor("#ff9800"), 2)
        pen.setCosmetic(True)
        painter.setPen(pen)

        for entity in highlighted:
            if getattr(entity, "bounding_box3d", None).valid:
                self._draw_bounds(painter, entity.bounding_box3d)

        painter.setPen(QColor("#ffb74d"))
        painter.drawText(QPointF(12, 184), f"Exchange Validation: {len(highlighted)} highlighted")

    # --------------------------------

    def _draw_compare_results(self, painter, workspace):

        results = (
            workspace.visible_compare_results()
            if hasattr(workspace, "visible_compare_results")
            else []
        )

        if not results:
            return

        style = self._visual_style(workspace)

        for result in results:
            color = QColor(getattr(result, "display_color", "#ffca28"))

            if getattr(result, "selected", False):
                color = QColor(getattr(style, "selection_color", "#ffeb3b"))
            elif getattr(result, "hovered", False):
                color = QColor(getattr(style, "hover_color", "#80deea"))

            pen = QPen(color, 3 if getattr(result, "selected", False) else 2)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(QColor(color))

            for start, end in result.segments():
                self._draw_line(painter, start, end)

            box = getattr(result, "bounding_box3d", None)

            if box is not None and box.valid:
                self._draw_bounds(painter, box)

            screen = self.camera.project(result.location)

            if screen is not None:
                painter.drawText(
                    QPointF(screen[0] + 8, screen[1] - 8),
                    f"{result.change_type}: {result.name}",
                )

        painter.setPen(QColor("#ce93d8"))
        painter.drawText(QPointF(12, 204), f"Compare: {len(results)} changes")

    # --------------------------------

    def _draw_revisions(self, painter, workspace):

        revisions = (
            workspace.visible_revisions()
            if hasattr(workspace, "visible_revisions")
            else []
        )

        if not revisions:
            return

        style = self._visual_style(workspace)
        manager = getattr(workspace, "revision_manager", None)
        active = getattr(manager, "active_revision", None)

        for revision in revisions:
            color = QColor(getattr(revision, "display_color", "#7e57c2"))

            if getattr(revision, "selected", False):
                color = QColor(getattr(style, "selection_color", "#ffeb3b"))
            elif active is revision:
                color = QColor("#ce93d8")
            elif getattr(revision, "hovered", False):
                color = QColor(getattr(style, "hover_color", "#80deea"))

            pen = QPen(color, 3 if getattr(revision, "selected", False) or active is revision else 2)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(QColor(color))

            for start, end in revision.segments():
                self._draw_line(painter, start, end)

            screen = self.camera.project(revision.location)

            if screen is not None:
                painter.drawEllipse(QPointF(screen[0], screen[1]), 4, 4)
                painter.drawText(
                    QPointF(screen[0] + 8, screen[1] - 8),
                    f"Revision: {revision.name}",
                )

        summary = manager.summary() if manager is not None else {"revisions": len(revisions)}
        painter.setPen(QColor("#b39ddb"))
        painter.drawText(QPointF(12, 224), f"Revisions: {summary.get('revisions', len(revisions))}")

    # --------------------------------

    def _draw_coordination_packages(self, painter, workspace):

        packages = (
            workspace.visible_coordination_packages()
            if hasattr(workspace, "visible_coordination_packages")
            else []
        )

        if not packages:
            return

        style = self._visual_style(workspace)
        manager = getattr(workspace, "coordination_package_manager", None)
        active = getattr(manager, "active_package", None)

        for package in packages:
            color = QColor(getattr(package, "display_color", "#8bc34a"))

            if getattr(package, "selected", False):
                color = QColor(getattr(style, "selection_color", "#ffeb3b"))
            elif active is package:
                color = QColor("#aed581")
            elif getattr(package, "hovered", False):
                color = QColor(getattr(style, "hover_color", "#80deea"))

            pen = QPen(color, 3 if getattr(package, "selected", False) or active is package else 2)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(QColor(color))

            for start, end in package.segments():
                self._draw_line(painter, start, end)

            screen = self.camera.project(package.location)

            if screen is not None:
                painter.drawText(
                    QPointF(screen[0] + 8, screen[1] - 8),
                    f"Package: {package.name} [{package.validation.status}]",
                )

        painter.setPen(QColor("#c5e1a5"))
        painter.drawText(QPointF(12, 244), f"Packages: {len(packages)}")

    # --------------------------------

    def _draw_bim(self, painter, workspace):

        items = (
            workspace.visible_bim_objects()
            if hasattr(workspace, "visible_bim_objects")
            else []
        )

        if not items:
            return

        style = self._visual_style(workspace)
        manager = getattr(workspace, "bim_manager", None)

        for item in items:
            color = self._bim_color(item, manager)

            if getattr(item, "selected", False):
                color = QColor(getattr(style, "selection_color", "#ffeb3b"))
            elif self._bim_related_to_selection(item, workspace):
                color = QColor("#ba68c8")
            elif getattr(item, "hovered", False):
                color = QColor(getattr(style, "hover_color", "#80deea"))

            pen = QPen(color, 3 if getattr(item, "selected", False) else 1)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(QColor(color))

            for start, end in item.segments():
                self._draw_line(painter, start, end)

            for point in item.points():
                self._draw_point(painter, point, color)

            location = getattr(item, "location", None)
            if location is not None:
                screen = self.camera.project(location)

                if screen is not None:
                    painter.drawText(
                        QPointF(screen[0] + 8, screen[1] - 8),
                        f"BIM: {item.name}",
                    )

        painter.setPen(QColor("#80cbc4"))
        painter.drawText(QPointF(12, 264), f"BIM Objects: {len(items)}")

    # --------------------------------

    def _draw_products(self, painter, workspace):

        items = (
            workspace.visible_product_objects()
            if hasattr(workspace, "visible_product_objects")
            else []
        )

        if not items:
            return

        style = self._visual_style(workspace)
        manager = getattr(workspace, "product_manager", None)

        for item in items:
            color = self._product_color(item, manager)

            if getattr(item, "selected", False):
                color = QColor(getattr(style, "selection_color", "#ffeb3b"))
            elif self._product_related_to_selection(item, workspace):
                color = QColor("#64ffda")
            elif getattr(item, "hovered", False):
                color = QColor(getattr(style, "hover_color", "#80deea"))

            pen = QPen(color, 3 if getattr(item, "selected", False) else 1)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(QColor(color))

            for start, end in item.segments():
                self._draw_line(painter, start, end)

            for point in item.points():
                self._draw_point(painter, point, color)

            location = getattr(item, "location", None)
            if location is not None:
                screen = self.camera.project(location)

                if screen is not None:
                    painter.drawText(
                        QPointF(screen[0] + 8, screen[1] - 8),
                        f"Product: {item.name}",
                    )

        painter.setPen(QColor("#90caf9"))
        painter.drawText(QPointF(12, 284), f"Product Objects: {len(items)}")

    # --------------------------------

    def _product_color(self, item, manager):

        color = getattr(item, "display_color", "#64b5f6")

        if manager is None:
            return QColor(color)

        if getattr(item, "is_parametric_session", False):
            if getattr(getattr(item, "dirty_state", None), "dirty", False):
                return QColor("#ffca28")
            if getattr(getattr(item, "freeze_state", None), "frozen", False):
                return QColor("#90a4ae")
            return QColor(color)

        if getattr(item, "is_parametric_engine", False) or getattr(item, "is_parametric_document", False):
            return QColor(color)

        if getattr(item, "is_live_solver", False):
            flags = getattr(item, "flags", None)
            state = getattr(item, "state", None)
            if getattr(flags, "blocked", False) or getattr(state, "state", "") == "Blocked":
                return QColor("#ef5350")
            if getattr(flags, "queued", False) or getattr(state, "evaluation_state", "") == "Queued":
                return QColor("#ffca28")
            if getattr(flags, "paused", False) or getattr(flags, "frozen", False):
                return QColor("#90a4ae")
            return QColor(color)

        if getattr(item, "is_solver_session", False):
            state = getattr(item, "state", None)
            if getattr(state, "evaluation_state", "") in ("Blocked", "Failed"):
                return QColor("#ef5350")
            if getattr(state, "evaluation_state", "") in ("Queued", "Pending"):
                return QColor("#ffca28")
            return QColor(color)

        if getattr(item, "is_evaluation_request", False) or getattr(item, "is_evaluation_batch", False) or getattr(item, "is_evaluation_result", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "failed", False) or getattr(flags, "blocked", False):
                return QColor("#ef5350")
            if getattr(flags, "queued", False) or getattr(flags, "pending", False):
                return QColor("#ffca28")
            if getattr(flags, "completed", False):
                return QColor("#66bb6a")
            return QColor(color)

        if getattr(item, "is_visual_node_graph", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "dirty", False):
                return QColor("#ffca28")
            if getattr(flags, "frozen", False):
                return QColor("#90a4ae")
            return QColor("#42a5f5")

        if getattr(item, "is_visual_node", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "dirty", False):
                return QColor("#ffca28")
            if getattr(flags, "validation_status", "") == "Invalid":
                return QColor("#ef5350")
            return QColor("#26c6da")

        if getattr(item, "is_visual_node_port", False):
            return QColor("#4dd0e1")

        if getattr(item, "is_node_connection", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "validation_status", "") == "Invalid":
                return QColor("#ef5350")
            return QColor("#7e57c2")

        if getattr(item, "is_visual_node_graph_item", False):
            return QColor("#90caf9")

        if getattr(item, "is_data_tree", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "dirty", False):
                return QColor("#ffca28")
            if getattr(flags, "frozen", False):
                return QColor("#90a4ae")
            if getattr(flags, "validation_status", "") == "Invalid":
                return QColor("#ef5350")
            return QColor("#66bb6a")

        if getattr(item, "is_data_branch", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "dirty", False):
                return QColor("#ffca28")
            return QColor("#81c784")

        if getattr(item, "is_data_path", False):
            return QColor("#a5d6a7")

        if getattr(item, "is_data_item", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "validation_status", "") == "Invalid":
                return QColor("#ef5350")
            return QColor("#c5e1a5")

        if getattr(item, "is_data_container", False):
            return QColor("#aed581")

        if getattr(item, "is_data_flow", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "validation_status", "") == "Invalid":
                return QColor("#ef5350")
            return QColor("#9ccc65")

        if getattr(item, "is_cad_node_library", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "validation_status", "") == "Invalid":
                return QColor("#ef5350")
            return QColor("#ffb74d")

        if getattr(item, "is_cad_node_category", False):
            return QColor("#ffcc80")

        if getattr(item, "is_cad_node_definition", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "dirty", False):
                return QColor("#ffca28")
            if getattr(flags, "validation_status", "") == "Invalid":
                return QColor("#ef5350")
            return QColor("#ffa726")

        if getattr(item, "is_cad_node_template", False):
            return QColor("#ffb300")

        if getattr(item, "is_bim_node_library", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "validation_status", "") == "Invalid":
                return QColor("#ef5350")
            return QColor("#8d6e63")

        if getattr(item, "is_bim_node_category", False):
            return QColor("#a1887f")

        if getattr(item, "is_bim_node_definition", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "dirty", False):
                return QColor("#ffca28")
            if getattr(flags, "validation_status", "") == "Invalid":
                return QColor("#ef5350")
            return QColor("#795548")

        if getattr(item, "is_bim_node_template", False):
            return QColor("#bcaaa4")

        if getattr(item, "is_manufacturing_node_library", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "validation_status", "") == "Invalid":
                return QColor("#ef5350")
            return QColor("#26a69a")

        if getattr(item, "is_manufacturing_node_category", False):
            return QColor("#4db6ac")

        if getattr(item, "is_manufacturing_node_definition", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "dirty", False):
                return QColor("#ffca28")
            if getattr(flags, "validation_status", "") == "Invalid":
                return QColor("#ef5350")
            return QColor("#00897b")

        if getattr(item, "is_manufacturing_node_template", False):
            return QColor("#80cbc4")

        if getattr(item, "is_ai_node_library", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "validation_status", "") == "Invalid":
                return QColor("#ef5350")
            return QColor("#5c6bc0")

        if getattr(item, "is_ai_node_category", False):
            return QColor("#7986cb")

        if getattr(item, "is_ai_node_definition", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "dirty", False):
                return QColor("#ffca28")
            if getattr(flags, "validation_status", "") == "Invalid":
                return QColor("#ef5350")
            return QColor("#3f51b5")

        if getattr(item, "is_ai_node_template", False):
            return QColor("#9fa8da")

        if getattr(item, "is_script_node_library", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "validation_status", "") == "Invalid":
                return QColor("#ef5350")
            return QColor("#7e57c2")

        if getattr(item, "is_script_node_category", False):
            return QColor("#9575cd")

        if getattr(item, "is_script_node_definition", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "dirty", False):
                return QColor("#ffca28")
            if getattr(flags, "validation_status", "") == "Invalid":
                return QColor("#ef5350")
            return QColor("#6a1b9a")

        if getattr(item, "is_script_node_template", False):
            return QColor("#b39ddb")

        if getattr(item, "is_preview_session", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "dirty", False) or getattr(flags, "queued", False):
                return QColor("#ffca28")
            return QColor("#00acc1")

        if getattr(item, "is_preview_request", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "dirty", False) or getattr(flags, "queued", False):
                return QColor("#ffca28")
            return QColor("#26c6da")

        if getattr(item, "is_preview_template", False):
            return QColor("#80deea")

        if getattr(item, "is_workspace_synchronization", False):
            return QColor("#4dd0e1")

        if getattr(item, "is_viewport_synchronization", False):
            metadata = getattr(item, "metadata", None)
            if getattr(metadata, "viewport_dirty", False) or getattr(metadata, "refresh_requested", False):
                return QColor("#ffca28")
            return QColor("#00bcd4")

        if getattr(item, "is_property_synchronization", False):
            return QColor("#4fc3f7")

        if getattr(item, "is_update_coordination", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "dirty", False) or getattr(flags, "queued", False):
                return QColor("#ffca28")
            return QColor("#29b6f6")

        if getattr(item, "is_execution_engine", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "failed", False):
                return QColor("#ef5350")
            if getattr(flags, "running", False):
                return QColor("#42a5f5")
            if getattr(flags, "queued", False) or getattr(flags, "dirty", False):
                return QColor("#ffca28")
            return QColor("#00c853")

        if getattr(item, "is_execution_session", False):
            state = getattr(item, "state", None)
            if getattr(state, "status", "") == "Failed":
                return QColor("#ef5350")
            if getattr(state, "running", False):
                return QColor("#42a5f5")
            return QColor("#00acc1")

        if getattr(item, "is_feature_execution_session", False):
            state = getattr(item, "state", None)
            diagnostics = getattr(item, "diagnostics", None)
            if getattr(diagnostics, "error_ids", []):
                return QColor("#ef5350")
            if getattr(state, "suppressed", False):
                return QColor("#b0bec5")
            if getattr(state, "rolled_back", False):
                return QColor("#ffca28")
            return QColor("#ffa726")

        if getattr(item, "is_geometry_kernel", False):
            state = getattr(item, "state", None)
            diagnostics = getattr(item, "diagnostics", None)
            if getattr(state, "blocked", False) or getattr(diagnostics, "error_ids", []):
                return QColor("#ef5350")
            if getattr(state, "dirty", False):
                return QColor("#ffca28")
            if getattr(state, "state", "") == "Completed":
                return QColor("#66bb6a")
            return QColor("#558b2f")

        if getattr(item, "is_geometry_session", False):
            state = getattr(item, "state", None)
            if getattr(state, "state", "") == "Completed":
                return QColor("#8bc34a")
            if getattr(state, "blocked", False):
                return QColor("#ef5350")
            return QColor("#689f38")

        if getattr(item, "is_brep_topology", False) or getattr(item, "is_topology_element", False):
            diagnostics = getattr(item, "diagnostics", None)
            if getattr(diagnostics, "topology_valid", True) is False:
                return QColor("#ef5350")
            return QColor("#9ccc65")

        if getattr(item, "is_geometry_pipeline", False) or getattr(item, "is_geometry_result", False):
            return QColor("#7cb342")

        if getattr(item, "is_execution_request", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "failed", False):
                return QColor("#ef5350")
            if getattr(flags, "completed", False):
                return QColor("#66bb6a")
            if getattr(flags, "running", False):
                return QColor("#42a5f5")
            return QColor("#ffca28")

        if getattr(item, "is_execution_result", False):
            if getattr(item, "status", "") == "Failed":
                return QColor("#ef5350")
            return QColor("#66bb6a")

        if getattr(item, "is_execution_batch", False):
            return QColor("#26c6da")

        if getattr(item, "is_execution_pipeline", False):
            return QColor("#7e57c2")

        if getattr(item, "is_execution_history", False):
            return QColor("#80cbc4")

        if getattr(item, "is_parametric_parameter", False):
            if getattr(item, "scope", "") == "Computed":
                return QColor("#ffb74d")
            return QColor(color)

        if getattr(item, "is_expression", False) or getattr(item, "is_expression_binding", False):
            return QColor(color)

        if getattr(item, "is_dependency_graph", False):
            flags = getattr(item, "flags", None)
            if getattr(flags, "dirty", False) or getattr(flags, "pending_evaluation", False):
                return QColor("#fbc02d")
            return QColor("#7e57c2")

        if getattr(item, "is_dependency_node", False):
            if getattr(item, "dirty", False) or getattr(item, "pending_evaluation", False):
                return QColor("#ffa726")
            return QColor("#9575cd")

        if getattr(item, "is_dependency_edge", False) or getattr(item, "is_dependency_path", False):
            return QColor("#5c6bc0")

        if getattr(item, "is_dependency_topology", False):
            return QColor("#26a69a")

        if getattr(item, "type_name", "") == "Component":
            category = manager.component_category_for(item)

            if category is not None:
                return QColor(getattr(category, "color", color))

        material = manager.engineering_material_for(item)

        if material is not None:
            return QColor(getattr(material, "color", color))

        components = manager.components_for(item)

        if components:
            category = manager.component_category_for(components[0])

            if category is not None:
                return QColor(getattr(category, "color", color))

        return QColor(color)

    # --------------------------------

    def _product_related_to_selection(self, item, workspace):

        selected = getattr(getattr(workspace, "selection", None), "selected", [])
        manager = getattr(workspace, "product_manager", None)

        if manager is None:
            return False

        for selected_item in selected:
            if not getattr(selected_item, "is_product", False):
                continue

            if item is selected_item:
                continue

            if getattr(item, "type_name", "") == "ProductPart":
                components = manager.components_for(item)
                if selected_item in components:
                    return True

            if getattr(selected_item, "type_name", "") == "ProductPart":
                components = manager.components_for(selected_item)
                if item in components:
                    return True

            if getattr(item, "part_id", "") and getattr(item, "part_id", "") == getattr(selected_item, "part_id", ""):
                return True

        return False

    # --------------------------------

    def _bim_color(self, item, manager):

        color = getattr(item, "display_color", "#b0bec5")

        if manager is None:
            return QColor(color)

        project = getattr(manager, "active_project", None)

        if project is None:
            return QColor(color)

        classifications = manager.classifications_for(item)

        if classifications:
            return QColor("#26c6da")

        if manager.openings_for(item):
            return QColor("#ff7043")

        if manager.hosted_objects_for(item):
            return QColor("#66bb6a")

        if manager.connections_for(item):
            return QColor("#42a5f5")

        if manager.design_options_for(item):
            return QColor("#ffee58")

        if manager.phase_assignment_for(item) is not None:
            return QColor("#26a69a")

        if manager.lifecycle_state_for(item) is not None:
            return QColor("#8d6e63")

        if manager.rooms_for(item):
            return QColor("#ffb74d")

        if manager.spaces_for(item):
            return QColor("#4dd0e1")

        if manager.zones_for(item):
            return QColor("#9575cd")

        if manager.area_regions_for(item):
            return QColor("#aed581")

        if manager.mep_systems_for(item):
            return QColor("#29b6f6")

        if manager.connectors_for(item):
            return QColor("#ec407a")

        if manager.mep_networks_for(item):
            return QColor("#5c6bc0")

        if manager.validation_results_for(item):
            return QColor("#ef5350")

        if manager.model_check_results_for(item):
            return QColor("#ffa726")

        has_interoperability_metadata = bool(
            getattr(project, "exchange_profiles", []) or
            getattr(project, "exchange_rules", [])
        )
        interoperability = (
            manager.interoperability_status_for(item)
            if has_interoperability_metadata
            else {}
        )

        if interoperability and any(not value for value in interoperability.values()):
            return QColor("#90a4ae")

        if manager.relationships_for(item):
            color = "#ab47bc"

        if manager.ifc_status_for(item) == "Linked":
            color = "#7e57c2"

        material = manager.material_for(item)

        if material is not None:
            return QColor(getattr(material, "color", color))

        element_category = manager.element_category_for(item)

        if element_category is not None:
            return QColor(getattr(element_category, "color", color))

        family = manager.family_library.get_family(getattr(item, "family_id", ""))

        if family is not None:
            category = next(
                (
                    value for value in project.categories
                    if value.id == getattr(family, "category_id", "")
                ),
                None,
            )
            return QColor(getattr(category, "color", color))

        category = next(
            (
                value for value in project.categories
                if value.id == getattr(item, "category_id", "")
            ),
            None,
        )

        return QColor(getattr(category, "color", color))

    # --------------------------------

    def _bim_related_to_selection(self, item, workspace):

        selected = getattr(getattr(workspace, "selection", None), "selected", [])
        manager = getattr(workspace, "bim_manager", None)

        for selected_item in selected:
            if not getattr(selected_item, "is_bim", False):
                continue

            if manager is not None:
                related = manager.related_elements(selected_item)

                if item in related:
                    return True

                selected_assemblies = manager.assemblies_for(selected_item)
                item_assemblies = manager.assemblies_for(item)

                if any(assembly in item_assemblies for assembly in selected_assemblies):
                    return True

                selected_material = manager.material_for(selected_item)
                item_material = manager.material_for(item)

                if selected_material is not None and selected_material is item_material:
                    return True

                if manager.ifc_status_for(selected_item) == "Linked" and manager.ifc_status_for(item) == "Linked":
                    return True

                selected_classifications = manager.classifications_for(selected_item)
                item_classifications = manager.classifications_for(item)
                selected_codes = {(mapping.system_id, mapping.code) for mapping in selected_classifications}
                item_codes = {(mapping.system_id, mapping.code) for mapping in item_classifications}

                if selected_codes and selected_codes.intersection(item_codes):
                    return True

                selected_schedules = manager.schedules_for(selected_item)
                item_schedules = manager.schedules_for(item)

                if any(schedule in item_schedules for schedule in selected_schedules):
                    return True

                if item in manager.hosted_objects_for(selected_item):
                    return True

                if manager.host_for(selected_item) is item:
                    return True

                if any(opening in manager.openings_for(item) for opening in manager.openings_for(selected_item)):
                    return True

                if item in manager.connected_items(selected_item):
                    return True

                selected_options = {membership.option_id for membership in manager.design_options_for(selected_item)}
                item_options = {membership.option_id for membership in manager.design_options_for(item)}

                if selected_options and selected_options.intersection(item_options):
                    return True

                selected_phase = manager.phase_assignment_for(selected_item)
                item_phase = manager.phase_assignment_for(item)

                if selected_phase is not None and item_phase is not None and selected_phase.created_phase_id == item_phase.created_phase_id:
                    return True

                selected_lifecycle = manager.lifecycle_state_for(selected_item)
                item_lifecycle = manager.lifecycle_state_for(item)

                if selected_lifecycle is not None and selected_lifecycle is item_lifecycle:
                    return True

                selected_rooms = manager.rooms_for(selected_item)
                item_rooms = manager.rooms_for(item)
                if any(room in item_rooms for room in selected_rooms):
                    return True

                selected_spaces = manager.spaces_for(selected_item)
                item_spaces = manager.spaces_for(item)
                if any(space in item_spaces for space in selected_spaces):
                    return True

                selected_zones = manager.zones_for(selected_item)
                item_zones = manager.zones_for(item)
                if any(zone in item_zones for zone in selected_zones):
                    return True

                selected_mep_systems = manager.mep_systems_for(selected_item)
                item_mep_systems = manager.mep_systems_for(item)
                if any(system in item_mep_systems for system in selected_mep_systems):
                    return True

                selected_mep_networks = manager.mep_networks_for(selected_item)
                item_mep_networks = manager.mep_networks_for(item)
                if any(network in item_mep_networks for network in selected_mep_networks):
                    return True

                selected_validation = manager.validation_results_for(selected_item)
                item_validation = manager.validation_results_for(item)
                if selected_validation and item_validation:
                    return True

                selected_checks = manager.model_check_results_for(selected_item)
                item_checks = manager.model_check_results_for(item)
                if selected_checks and item_checks:
                    return True

            if getattr(item, "element_definition_id", "") and getattr(item, "element_definition_id", "") == getattr(selected_item, "element_definition_id", ""):
                return True

            if getattr(item, "family_id", "") and getattr(item, "family_id", "") == getattr(selected_item, "family_id", ""):
                return True

            if getattr(item, "type_id", "") and getattr(item, "type_id", "") == getattr(selected_item, "type_id", ""):
                return True

        return False

    # --------------------------------

    def _draw_issues(self, painter, workspace):

        issues = (
            workspace.visible_issues()
            if hasattr(workspace, "visible_issues")
            else []
        )
        style = self._visual_style(workspace)

        for issue in issues:
            color = QColor(getattr(issue, "display_color", "#ff7043"))

            if getattr(issue, "selected", False):
                color = QColor(getattr(style, "selection_color", "#ffeb3b"))

            pen = QPen(color, 3 if getattr(issue, "selected", False) else 2)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(QColor(color))

            for start, end in issue.segments():
                self._draw_line(painter, start, end)

            self._draw_point(painter, issue.position, color)
            screen = self.camera.project(issue.position)

            if screen is not None:
                painter.drawText(
                    QPointF(screen[0] + 8, screen[1] - 8),
                    f"{issue.title} [{issue.status}]",
                )

    # --------------------------------

    def _draw_session_overlay(self, painter, workspace):

        manager = getattr(workspace, "collaboration_manager", None)

        if manager is None or not manager.settings.show_session_overlay:
            return

        active = getattr(manager, "active", None)

        if active is None:
            return

        painter.setPen(QColor("#b0bec5"))
        painter.drawText(QPointF(12, 104), f"Session: {active.name} | {active.status}")

    # --------------------------------

    def _draw_analysis_overlays(self, painter, workspace, entities):

        manager = getattr(workspace, "section_manager", None)
        display_mode = self._display_mode(workspace)

        if manager is None:
            return

        analysis = manager.analysis
        bounding_overlay = analysis.bounding_box_overlay or display_mode == "analysis_overlay"
        edge_overlay = analysis.edge_overlay or display_mode == "analysis_overlay"
        vertex_display = analysis.vertex_display or display_mode == "analysis_overlay"

        if analysis.object_bounds or bounding_overlay:
            pen = QPen(QColor("#90a4ae"), 1)
            pen.setCosmetic(True)
            painter.setPen(pen)

            for entity in entities:
                if not getattr(entity, "selected", False):
                    self._draw_bounds(painter, entity.bounding_box3d)

        if analysis.selection_bounds:
            pen = QPen(QColor("#ffeb3b"), 2)
            pen.setCosmetic(True)
            painter.setPen(pen)

            for entity in entities:
                if getattr(entity, "selected", False):
                    self._draw_bounds(painter, entity.bounding_box3d)

        if vertex_display:
            for entity in entities:
                for point in getattr(entity, "points", lambda: [])():
                    self._draw_point(painter, point, QColor("#f48fb1"))

        if edge_overlay or analysis.wireframe_overlay:
            pen = QPen(QColor("#b2ebf2"), 1)
            pen.setCosmetic(True)
            painter.setPen(pen)

            for entity in entities:
                for start, end in getattr(entity, "segments", lambda: [])():
                    self._draw_line(painter, start, end)

        if analysis.face_normals:
            pen = QPen(QColor("#ce93d8"), 1)
            pen.setCosmetic(True)
            painter.setPen(pen)

            for entity in entities:
                for start, end in manager.face_normal_segments(entity):
                    self._draw_line(painter, start, end)

        if analysis.back_faces:
            painter.setPen(QColor("#ff8a65"))
            painter.drawText(QPointF(12, 44), "Back-face visualization: enabled")

        if analysis.heatmap_enabled:
            painter.setPen(QColor("#ffcc80"))
            painter.drawText(QPointF(12, 64), f"Heatmap: {analysis.heatmap_mode}")

        self._draw_clip_preview(painter, manager)

    # --------------------------------

    def _draw_clip_preview(self, painter, manager):

        clipping = manager.clipping

        if not clipping.preview_enabled:
            return

        if clipping.box_enabled:
            box = type("ClipBox", (), {})()
            box.min = clipping.box_min
            box.max = clipping.box_max
            box.valid = True
            box.corners = lambda: [
                Vector3(x, y, z)
                for x in (box.min.x, box.max.x)
                for y in (box.min.y, box.max.y)
                for z in (box.min.z, box.max.z)
            ]
            pen = QPen(QColor("#ffab40"), 1)
            pen.setCosmetic(True)
            painter.setPen(pen)
            self._draw_bounds(painter, box)

    # --------------------------------

    def _is_snap_highlight(self, workspace, entity):

        snap_manager = getattr(workspace, "snap_manager3d", None)

        return (
            snap_manager is not None and
            snap_manager.highlighted_entity is entity
        )

    # --------------------------------

    def _display_mode(self, workspace, entity=None):

        manager = getattr(workspace, "display_mode_manager", None)

        if manager is not None:
            return manager.current_mode

        if entity is not None:
            return getattr(entity, "display_mode", "wireframe")

        return "wireframe"

    # --------------------------------

    def _visual_style(self, workspace):

        manager = getattr(workspace, "visual_style_manager", None)

        if manager is not None and manager.current is not None:
            return manager.current

        return type("DefaultVisualStyle", (), {
            "background": "#16191d",
            "grid_visible": True,
            "axis_visible": True,
            "edge_visible": True,
            "face_visible": True,
            "selection_color": "#ffeb3b",
            "hover_color": "#80deea",
            "snap_color": "#ffab40",
        })()

    # --------------------------------

    def _draw_line(self, painter, start, end):

        start_screen = self.camera.project(start)
        end_screen = self.camera.project(end)

        if start_screen is None or end_screen is None:
            return

        painter.drawLine(
            QPointF(start_screen[0], start_screen[1]),
            QPointF(end_screen[0], end_screen[1]),
        )

    # --------------------------------

    def _ucs_point(self, coordinate_system, x, y, z):

        point = Vector3(x, y, z)

        if coordinate_system is not None:
            return coordinate_system.to_world(point)

        return point

import math

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLineEdit,
    QWidget,
)

from engine.commands import (
    RotateEntity3DCommand,
    ScaleEntity3DCommand,
    TranslateEntity3DCommand,
    UpdateConstraintCommand,
    UpdateEntityCommand,
    UpdateLayerCommand,
)
from engine.geometry import Vector2, Vector3
from engine.geometry.curves import clone_points


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
        self.content = QLineEdit()
        self.alignment = QLineEdit()
        self.dimension_style = QLineEdit()

        self.color = QLineEdit()
        self.line_type = QLineEdit()
        self.line_weight = QLineEdit()

        self._add_rows(layout)
        self._configure_field_hints()
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
        layout.addRow("Text", self.content)
        layout.addRow("Alignment", self.alignment)
        layout.addRow("Dimension Style", self.dimension_style)
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
        self.content.editingFinished.connect(lambda: self._geometry_changed("content"))
        self.alignment.editingFinished.connect(lambda: self._geometry_changed("alignment"))
        self.dimension_style.editingFinished.connect(
            lambda: self._geometry_changed("dimension_style")
        )

        self.color.editingFinished.connect(lambda: self._layer_property_changed("color"))
        self.line_type.editingFinished.connect(
            lambda: self._layer_property_changed("line_type")
        )
        self.line_weight.editingFinished.connect(
            lambda: self._layer_property_changed("line_weight")
        )

    # -----------------------------------------

    def _configure_field_hints(self):
        """Add concise property hints without changing edit workflows."""

        self.type.setToolTip("Selected object type.")
        self.layer.setToolTip("Assign the selected object to an existing layer.")
        self.visible.setToolTip("Show or hide the selected object.")
        self.locked.setToolTip("Prevent edits to the selected object.")

        hints = {
            self.x: "X coordinate for the start, center, or first point.",
            self.y: "Y coordinate for the start, center, or first point.",
            self.x2: "X coordinate for the end or second point.",
            self.y2: "Y coordinate for the end or second point.",
            self.length: "Length, hatch scale, or related measurement.",
            self.angle: "Angle or rotation in degrees.",
            self.width: "Width or bounding-box X size.",
            self.height: "Height or bounding-box Y size.",
            self.radius: "Radius, measured value, or point count.",
            self.diameter: "Circle diameter.",
            self.content: "Text, pattern, override, or point list.",
            self.alignment: "Alignment, open/closed state, or status.",
            self.dimension_style: "Dimension style name.",
            self.color: "Layer color.",
            self.line_type: "Layer line type.",
            self.line_weight: "Layer line weight.",
        }

        for field, hint in hints.items():
            field.setPlaceholderText(hint)
            field.setToolTip(hint)

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

        if getattr(entity, "is_3d", False):
            if getattr(entity, "is_coordination_package", False):
                self._show_coordination_package(entity)
            elif getattr(entity, "is_product", False):
                self._show_product_object(entity)
            elif getattr(entity, "is_bim", False):
                self._show_bim_object(entity)
            elif getattr(entity, "is_revision", False):
                self._show_revision(entity)
            elif getattr(entity, "is_compare", False):
                self._show_compare_result(entity)
            elif getattr(entity, "is_bcf", False):
                self._show_bcf_topic(entity)
            elif getattr(entity, "is_clash", False):
                self._show_clash(entity)
            elif getattr(entity, "is_reference", False):
                self._show_reference(entity)
            elif getattr(entity, "is_issue", False):
                self._show_issue(entity)
            elif getattr(entity, "is_annotation3d", False):
                self._show_annotation3d(entity)
            elif getattr(entity, "is_section", False):
                self._show_section(entity)
            elif getattr(entity, "is_measurement", False):
                self._show_measurement(entity)
            else:
                self._show_3d_entity(entity)
        elif getattr(entity, "is_constraint", False):
            self._show_constraint(entity)
        elif getattr(entity, "is_hatch", False):
            self._show_hatch(entity)
        elif getattr(entity, "is_curve", False):
            self._show_curve(entity)
        elif getattr(entity, "is_dimension", False):
            self._show_dimension(entity)
        elif hasattr(entity, "start") and hasattr(entity, "end"):
            self._show_line(entity)
        elif hasattr(entity, "p1") and hasattr(entity, "p2"):
            self._show_rectangle(entity)
        elif hasattr(entity, "center") and hasattr(entity, "radius"):
            self._show_circle(entity)
        elif hasattr(entity, "text_entity"):
            self._show_leader(entity)
        elif hasattr(entity, "box_width") and hasattr(entity, "box_height"):
            self._show_mtext(entity)
        elif hasattr(entity, "position") and hasattr(entity, "text"):
            self._show_text(entity)

    # -----------------------------------------

    def _show_line(self, entity):

        self._set_point_pair(entity.start, entity.end)
        dx = entity.end.x - entity.start.x
        dy = entity.end.y - entity.start.y
        self.length.setText(self._number(math.hypot(dx, dy)))
        self.angle.setText(self._number(math.degrees(math.atan2(dy, dx))))

    # -----------------------------------------

    def _show_3d_entity(self, entity):

        self.type.setText(getattr(entity, "type_name", "Entity3D"))
        self.visible.setChecked(getattr(entity, "visible", True))
        self.locked.setChecked(getattr(entity, "locked", False))
        self._populate_layers(getattr(entity, "layer_name", ""))
        self._show_layer_properties(entity)

        points = entity.points()
        position = getattr(entity, "position3d", Vector3())
        rotation = getattr(entity, "rotation3d", Vector3())
        scale = getattr(entity, "scale3d", Vector3(1.0, 1.0, 1.0))

        self.x.setText(self._number(position.x))
        self.y.setText(self._number(position.y))
        self.content.setText(f"Z: {self._number(position.z)}")
        self.length.setText(self._number(rotation.x))
        self.angle.setText(self._number(rotation.y))
        self.radius.setText(self._number(rotation.z))
        self.width.setText(self._number(scale.x))
        self.height.setText(self._number(scale.y))
        self.diameter.setText(self._number(scale.z))

        gizmo = getattr(self.workspace, "transform_gizmo", None)
        coordinate_manager = getattr(self.workspace, "coordinate_system_manager", None)
        plane_manager = getattr(self.workspace, "construction_plane_manager", None)
        view_manager = getattr(self.workspace, "view_state_manager", None)
        display_manager = getattr(self.workspace, "display_mode_manager", None)
        style_manager = getattr(self.workspace, "visual_style_manager", None)
        collection_manager = getattr(self.workspace, "scene_collection_manager", None)
        filter_manager = getattr(self.workspace, "view_filter_manager", None)
        preset_manager = getattr(self.workspace, "display_preset_manager", None)

        if gizmo is not None:
            self.alignment.setText(f"{gizmo.coordinate_mode} {gizmo.pivot_mode}")

        if coordinate_manager is not None:
            active = getattr(coordinate_manager, "active", None)
            self.dimension_style.setText(f"UCS: {getattr(active, 'name', 'WCS')}")

        if plane_manager is not None:
            active_plane = getattr(plane_manager, "active", None)
            self.line_type.setText(f"Plane: {getattr(active_plane, 'name', 'XY Plane')}")

        if view_manager is not None:
            current_view = getattr(view_manager, "current", None)
            self.content.setText(f"{self.content.text()} | View: {getattr(current_view, 'name', 'Unsaved')}")

        if display_manager is not None:
            self.line_weight.setText(f"Display: {display_manager.current_mode}")

        if style_manager is not None:
            current_style = getattr(style_manager, "current", None)
            self.color.setText(f"Style: {getattr(current_style, 'name', 'Default')}")

        if points:
            first = points[0]
            self.x2.setText(self._number(first.x))
            self.y2.setText(self._number(first.y))

        if getattr(entity, "type_name", "") == "MeshEntity":
            display_mode = getattr(entity, "display_mode", "wireframe")
            primitive_type = getattr(entity, "primitive_type", None)
            prefix = f"Primitive: {primitive_type} | " if primitive_type else ""
            self.content.setText(f"{prefix}Display: {display_mode}")
            self.alignment.setText(
                f"Vertices: {len(entity.mesh_data.vertices)}  Faces: {len(entity.mesh_data.faces)}"
            )

        if len(points) > 1:
            last = points[-1]
            self.x2.setText(self._number(last.x))
            self.y2.setText(self._number(last.y))
            self.length.setText(self._number(points[0].distance_to(last)))

        box = entity.bounding_box3d

        if box.valid:
            size = box.size
            self.width.setText(self._number(size.x))
            self.height.setText(self._number(size.y))
            self.radius.setText(self._number(size.z))

        if collection_manager is not None:
            collection = collection_manager.entity_collection(entity)
            if collection is not None:
                self.content.setText(f"Collection: {collection.name}")

        if filter_manager is not None:
            active_filter = getattr(filter_manager, "active", None)
            if active_filter is not None:
                self.alignment.setText(f"Filter: {active_filter.name}")

        if preset_manager is not None:
            active_preset = getattr(preset_manager, "active", None)
            if active_preset is not None:
                self.dimension_style.setText(f"Preset: {active_preset.name}")

    # -----------------------------------------

    def _show_measurement(self, measurement):

        self.type.setText(getattr(measurement, "type_name", "Measurement"))
        self.content.setText(measurement.measurement_type)
        self.length.setText(str(measurement.result.value))
        self.alignment.setText(measurement.result.label)
        self.dimension_style.setText(measurement.result.units)

        if measurement.points:
            first = measurement.points[0]
            self.x.setText(self._number(first.x))
            self.y.setText(self._number(first.y))
            self.x2.setText(self._number(first.z))

    # -----------------------------------------

    def _show_bim_object(self, item):

        self.type.setText(getattr(item, "type_name", "BIMObject"))
        self.content.setText(getattr(item, "name", "BIM Object"))
        self.visible.setChecked(getattr(item, "visible", True))
        self.locked.setChecked(getattr(item, "locked", False))
        self._populate_layers(getattr(item, "layer_name", ""))
        self._show_layer_properties(item)

        manager = getattr(self.workspace, "bim_manager", None)
        project = getattr(manager, "active_project", None)
        category = None
        item_type = None
        family = None
        element_definition = None
        element_category = None
        level = None
        building = None

        if project is not None:
            category = next(
                (
                    value for value in project.categories
                    if value.id == getattr(item, "category_id", "")
                ),
                None,
            )
            item_type = next(
                (
                    value for value in project.types
                    if value.id == getattr(item, "type_id", "")
                ),
                None,
            )
            family = next(
                (
                    value for value in project.families
                    if value.id == getattr(item, "family_id", "")
                ),
                None,
            )
            element_definition = next(
                (
                    value for value in project.element_definitions
                    if value.id == getattr(item, "element_definition_id", "")
                ),
                None,
            )
            element_category = (
                manager.element_category_for(item)
                if manager is not None else None
            )
            level = next(
                (
                    value for value in project.levels
                    if value.id == getattr(item, "level_id", "")
                ),
                None,
            )
            building = next(
                (
                    value for value in project.buildings
                    if value.id == getattr(item, "building_id", "")
                ),
                None,
            )

        self.alignment.setText(f"Category: {getattr(category, 'name', 'BIM')}")
        self.dimension_style.setText(
            f"Family: {getattr(family, 'name', 'Unassigned')} | "
            f"Type: {getattr(item_type, 'name', getattr(item, 'type_name', 'BIM'))}"
        )
        self.line_type.setText(
            f"Element: {getattr(element_definition, 'kind', 'Unassigned')} | "
            f"Level: {getattr(level, 'name', 'Unassigned')}"
        )
        self.line_weight.setText(f"Building: {getattr(building, 'name', 'Unassigned')}")
        self.color.setText(
            getattr(element_category, "color", "") or
            getattr(item, "display_color", "")
        )

        guid = getattr(item, "guid", getattr(item, "id", ""))
        if guid:
            self.diameter.setText(f"GUID: {guid}")

        location = getattr(item, "location", Vector3())
        self.x.setText(self._number(location.x))
        self.y.setText(self._number(location.y))
        self.x2.setText(self._number(location.z))

        if hasattr(item, "elevation"):
            self.length.setText(self._number(item.elevation))
        if hasattr(item, "height"):
            self.height.setText(self._number(item.height))
        if hasattr(item, "spacing"):
            self.length.setText(self._number(item.spacing))
            self.width.setText(str(getattr(item, "count_x", "")))
            self.height.setText(str(getattr(item, "count_y", "")))

        property_sets = getattr(item, "property_sets", {})
        relationships = getattr(item, "relationships", {})
        manager_sets = manager.property_sets_for(item) if manager is not None else []
        resolved = (
            manager.resolved_instance_properties(item)
            if manager is not None and getattr(item, "type_name", "") == "BIMInstance"
            else {}
        )
        assemblies = manager.assemblies_for(item) if manager is not None else []

        if property_sets or relationships or manager_sets or resolved or assemblies:
            element_relationships = getattr(item, "element_relationships", None)
            relationship_count = (
                len(element_relationships.related_ids())
                if element_relationships is not None else
                len(relationships)
            )
            self.radius.setText(
                f"Psets: {len(property_sets) + len(manager_sets)}  "
                f"Properties: {len(resolved)}  Relations: {relationship_count}  "
                f"Assemblies: {len(assemblies)}"
            )

        element_parameters = getattr(item, "element_parameters", None)
        if element_parameters is not None and element_parameters.material:
            self.length.setText(f"Material: {element_parameters.material}")
        if element_parameters is not None and element_parameters.fire_rating:
            self.angle.setText(f"Fire: {element_parameters.fire_rating}")

        if getattr(item, "type_name", "") in ("FloorPlanView", "CeilingPlanView", "ElevationView", "SectionView", "DetailView", "View3D"):
            self.content.setText(f"View: {item.name}")
            self.alignment.setText(f"View Type: {item.view_type}")
            self.dimension_style.setText(f"Template: {getattr(item, 'template_id', '') or 'None'}")
            self.line_type.setText(f"Level: {getattr(level, 'name', 'Unassigned')}")
            self.line_weight.setText(f"Scale: {getattr(item, 'scale', '1:100')}")

        if getattr(item, "type_name", "") == "DrawingSheet":
            self.content.setText(f"Sheet: {item.number}")
            self.alignment.setText(f"Title Block: {item.title_block}")
            self.dimension_style.setText(f"Viewports: {len(item.viewport_references)}")
            self.line_type.setText("Documentation")
            self.line_weight.setText("Schedules / Legends ready")

        if getattr(item, "type_name", "") in ("Level", "GridSystem", "GridLine", "GridIntersection"):
            self.alignment.setText(getattr(item, "type_name", "BIM"))
            if hasattr(item, "elevation"):
                self.line_type.setText(f"Elevation: {self._number(item.elevation)}")
            if hasattr(item, "grid_line_ids"):
                self.dimension_style.setText(f"Grid Lines: {len(item.grid_line_ids)}")

        material = manager.material_for(item) if manager is not None else None
        if material is not None:
            self.length.setText(f"Material: {material.name}")
            self.color.setText(getattr(material, "color", self.color.text()))

        if manager is not None:
            quantity_stats = getattr(manager.active_project, "quantity_statistics", None)
            if quantity_stats is not None and quantity_stats.items:
                self.diameter.setText(
                    f"QTO Items: {quantity_stats.items}  "
                    f"Volume: {self._number(quantity_stats.total_volume)}"
                )

            classifications = manager.classifications_for(item)
            schedules = manager.schedules_for(item)
            ifc_status = manager.ifc_status_for(item)

            if classifications:
                self.alignment.setText(
                    f"Classifications: {len(classifications)}"
                )
            if schedules or ifc_status != "Unmapped":
                self.dimension_style.setText(
                    f"Schedules: {len(schedules)} | IFC: {ifc_status}"
                )

            relationships = manager.relationships_for(item)
            hosted = manager.hosted_objects_for(item)
            host = manager.host_for(item)
            openings = manager.openings_for(item)
            cuts = manager.cut_relationships_for(item)
            connections = manager.connections_for(item)

            if relationships or hosted or host is not None:
                self.radius.setText(
                    f"Relations: {len(relationships)}  "
                    f"Hosted: {len(hosted)}  "
                    f"Host: {getattr(host, 'name', 'None')}"
                )
            if openings or cuts or connections:
                self.diameter.setText(
                    f"Openings: {len(openings)}  Cuts: {len(cuts)}  "
                    f"Connections: {len(connections)}"
                )

            option_memberships = manager.design_options_for(item)
            phase_assignment = manager.phase_assignment_for(item)
            lifecycle_events = manager.lifecycle_events_for(item)
            lifecycle_state = manager.lifecycle_state_for(item)

            if option_memberships or phase_assignment is not None:
                self.line_type.setText(
                    f"Options: {len(option_memberships)}  "
                    f"Phase: {getattr(phase_assignment, 'created_phase_id', '') or 'Unassigned'}"
                )
            if lifecycle_events or lifecycle_state is not None:
                self.line_weight.setText(
                    f"Lifecycle: {getattr(lifecycle_state, 'name', 'Unassigned')}  "
                    f"Events: {len(lifecycle_events)}"
                )

            rooms = manager.rooms_for(item)
            spaces = manager.spaces_for(item)
            zones = manager.zones_for(item)
            area_regions = manager.area_regions_for(item)

            if rooms or spaces:
                self.length.setText(
                    f"Rooms: {len(rooms)}  Spaces: {len(spaces)}"
                )
            if zones or area_regions:
                self.angle.setText(
                    f"Zones: {len(zones)}  Area Regions: {len(area_regions)}"
                )

            mep_systems = manager.mep_systems_for(item)
            mep_networks = manager.mep_networks_for(item)
            connectors = manager.connectors_for(item)
            mep_coordination = manager.mep_coordination_for(item)

            if mep_systems or mep_networks or connectors:
                self.line_type.setText(
                    f"MEP Systems: {len(mep_systems)}  "
                    f"Networks: {len(mep_networks)}  "
                    f"Connectors: {len(connectors)}"
                )
            if any(mep_coordination.values()):
                self.line_weight.setText(
                    f"MEP Rules: {len(mep_coordination['rules'])}  "
                    f"Clearances: {len(mep_coordination['clearances'])}  "
                    f"Zones: {len(mep_coordination['service_zones'])}"
                )

            validation_results = manager.validation_results_for(item)
            model_check_results = manager.model_check_results_for(item)
            project = getattr(manager, "active_project", None)
            has_interoperability_metadata = bool(
                getattr(project, "exchange_profiles", []) or
                getattr(project, "exchange_rules", [])
            )
            interoperability = (
                manager.interoperability_status_for(item)
                if has_interoperability_metadata
                else {}
            )

            if validation_results or model_check_results:
                self.radius.setText(
                    f"Validation: {len(validation_results)}  "
                    f"Model Checks: {len(model_check_results)}"
                )
            if interoperability:
                ready = len([value for value in interoperability.values() if value])
                blocked = len([value for value in interoperability.values() if not value])
                self.diameter.setText(
                    f"Exchange Ready: {ready}  Blocked: {blocked}"
                )

    # -----------------------------------------

    def _show_product_object(self, item):

        self.type.setText(getattr(item, "type_name", "Product"))
        self.content.setText(getattr(item, "name", "Product"))
        self.color.setText(getattr(item, "display_color", self.color.text()))
        self._show_layer_properties(item)

        manager = getattr(self.workspace, "product_manager", None)
        location = getattr(item, "location", Vector3())
        self.x.setText(self._number(location.x))
        self.y.setText(self._number(location.y))
        self.x2.setText(self._number(location.z))

        if manager is None:
            return

        stats = manager.statistics()
        active = manager.active_document
        self.alignment.setText(
            f"Document: {getattr(active, 'name', 'Unassigned')}"
        )
        self.dimension_style.setText(
            f"Units: {getattr(active, 'units', 'mm')}  "
            f"Precision: {getattr(active, 'precision', 3)}"
        )
        self.diameter.setText(
            f"Parts: {stats.parts}  Components: {stats.components}"
        )

        if getattr(item, "type_name", "") == "ProductPart":
            components = manager.components_for(item)
            parameters = manager.parameters_for(item)
            parameter_sets = manager.parameter_sets_for(item)
            sketches = manager.sketches_for(item)
            bodies = manager.bodies_for(item)
            surface_bodies = manager.surface_bodies_for(item)
            curves = manager.curves_for(item)
            references = manager.reference_geometry_for(item)
            construction = manager.construction_geometry_for(item)
            mechanical_components = manager.mechanical_components_for_part(item)
            sheet_metal_parts = manager.sheet_metal_parts_for(item)
            analysis_results = manager.analysis_results_for(item)
            manufacturing_reports = manager.manufacturing_reports_for(item)
            product_reports = manager.product_reports_for(item)
            cam_jobs = [
                job for job in getattr(manager, "cam_jobs", [])
                if item.id in getattr(job, "target_ids", [])
            ]
            cam_setups = [
                setup for setup in getattr(manager, "cam_setups", [])
                if item.id in getattr(getattr(setup, "stock", None), "target_ids", [])
            ]
            cam_operations = [
                operation for operation in getattr(manager, "cam_operations", [])
                if item.id in getattr(operation, "target_ids", [])
            ]
            tool_profiles = [
                profile for profile in getattr(manager, "feed_speed_profiles", [])
                if profile.material_id == getattr(item, "engineering_material_id", "")
            ]
            features = manager.features_for(item)
            material = manager.engineering_material_for(item)
            mechanical_metadata = manager.mechanical_metadata_for(item)
            metadata = getattr(item, "metadata", None)
            self.radius.setText(
                f"Components: {len(components)}  "
                f"Parameters: {len(parameters)}  Sets: {len(parameter_sets)}  "
                f"Sketches: {len(sketches)}  Bodies: {len(bodies)}  "
                f"Surfaces: {len(surface_bodies)}  Curves: {len(curves)}  "
                f"Refs: {len(references)}  Construction: {len(construction)}  "
                f"Library: {len(mechanical_components)}  Sheet Metal: {len(sheet_metal_parts)}  "
                f"Analysis: {len(analysis_results)}  Mfg: {len(manufacturing_reports)}  "
                f"CAM Jobs: {len(cam_jobs)}  CAM Setups: {len(cam_setups)}  "
                f"CAM Ops: {len(cam_operations)}  "
                f"Tool Profiles: {len(tool_profiles)}  "
                f"Reports: {len(product_reports)}  "
                f"Features: {len(features)}"
            )
            self.line_type.setText(
                f"Mesh: {getattr(item, 'mesh_entity_name', '') or getattr(item, 'mesh_entity_id', '') or 'Referenced'}"
            )
            if material is not None:
                self.length.setText(f"Material: {material.name}")
                self.color.setText(getattr(material, "color", self.color.text()))
            if metadata is not None:
                self.line_weight.setText(
                    f"Material: {metadata.material or 'Unassigned'}"
                )
            if mechanical_metadata is not None:
                mass = getattr(mechanical_metadata, "mass", None)
                manufacturing = getattr(mechanical_metadata, "manufacturing", None)
                tolerance = getattr(mechanical_metadata, "tolerance", None)
                finish = getattr(mechanical_metadata, "finish", None)
                self.width.setText(
                    f"Mass: {self._number(getattr(mass, 'mass', 0.0))}"
                )
                self.height.setText(
                    f"Volume: {self._number(getattr(mass, 'volume', 0.0))}"
                )
                self.line_type.setText(
                    f"Process: {getattr(manufacturing, 'process', '') or 'Unassigned'}"
                )
                self.line_weight.setText(
                    f"Tolerance: {getattr(tolerance, 'tolerance_class', '') or 'Unassigned'}"
                )
                self.angle.setText(
                    f"Finish: {getattr(finish, 'surface_finish', '') or 'Unassigned'}"
                )
        elif getattr(item, "type_name", "") == "Component":
            component_type = manager.component_type_for(item)
            category = manager.component_category_for(item)
            metadata = getattr(item, "metadata", None)
            self.radius.setText(f"Part: {getattr(item, 'part_id', '') or 'Unassigned'}")
            self.line_type.setText(
                f"Type: {getattr(component_type, 'name', 'Unassigned')}"
            )
            self.line_weight.setText(
                f"Category: {getattr(category, 'name', 'Unassigned')}"
            )
            if metadata is not None and metadata.manufacturer:
                self.alignment.setText(f"Manufacturer: {metadata.manufacturer}")
        elif getattr(item, "is_sketch", False):
            geometry = manager.geometry_for_sketch(item)
            constraints = manager.constraints_for_sketch(item)
            dimensions = manager.dimensions_for_sketch(item)
            self.radius.setText(
                f"Geometry: {len(geometry)}  Constraints: {len(constraints)}  "
                f"Dimensions: {len(dimensions)}"
            )
            self.line_type.setText(
                f"Plane: {getattr(item, 'plane_id', '') or 'Unassigned'}"
            )
            self.line_weight.setText(
                "Active" if getattr(item, "active", False) else "Inactive"
            )
            self.angle.setText(
                f"Status: {getattr(getattr(item, 'metadata', None), 'status', 'Under Defined')}"
            )
        elif getattr(item, "is_sketch_geometry", False):
            self.radius.setText(f"Sketch: {getattr(item, 'sketch_id', '') or 'Unassigned'}")
            self.line_type.setText(f"Geometry: {getattr(item, 'geometry_type', 'Geometry')}")
            self.line_weight.setText(
                "Construction" if getattr(item, "construction", False) else "Real"
            )
            self.angle.setText("Centerline" if getattr(item, "centerline", False) else "")
        elif getattr(item, "is_sketch_constraint", False):
            self.radius.setText(f"Sketch: {getattr(item, 'sketch_id', '') or 'Unassigned'}")
            self.line_type.setText(f"Constraint: {getattr(item, 'constraint_type', '')}")
            self.line_weight.setText(
                "Enabled" if getattr(item, "enabled", True) else "Disabled"
            )
            self.angle.setText(
                f"Status: {getattr(getattr(item, 'metadata', None), 'status', 'Unsolved')}"
            )
        elif getattr(item, "is_sketch_dimension", False):
            self.radius.setText(f"Sketch: {getattr(item, 'sketch_id', '') or 'Unassigned'}")
            self.length.setText(
                f"{getattr(item, 'dimension_type', 'Dimension')}: "
                f"{self._number(getattr(item, 'value', 0.0))} {getattr(item, 'unit', '')}"
            )
            metadata = getattr(item, "metadata", None)
            if metadata is not None:
                self.line_type.setText("Driven" if metadata.driven else "Driving")
                self.line_weight.setText(f"Expression: {metadata.expression or 'None'}")
        elif getattr(item, "is_surface_body", False):
            features = [
                feature for feature in getattr(manager, "features", [])
                if feature.id in getattr(item, "feature_ids", [])
            ]
            metadata = getattr(item, "metadata", None)
            self.radius.setText(f"Surface Features: {len(features)}")
            self.line_type.setText(
                f"Mesh: {getattr(item, 'mesh_entity_id', '') or 'Unassigned'}"
            )
            self.line_weight.setText(
                "Visible" if getattr(item, "visible", True) else "Hidden"
            )
            self.width.setText(
                f"Group: {getattr(metadata, 'group', '') or 'Unassigned'}"
            )
        elif getattr(item, "is_curve", False):
            definition = getattr(item, "definition", None)
            metadata = getattr(item, "metadata", None)
            marker_points = getattr(definition, "marker_points", [])
            references = (
                len(getattr(definition, "profile_ids", [])) +
                len(getattr(definition, "sketch_geometry_ids", [])) +
                len(getattr(definition, "body_ids", [])) +
                len(getattr(definition, "surface_body_ids", [])) +
                len(getattr(definition, "mesh_entity_ids", [])) +
                len(getattr(definition, "reference_ids", []))
            )
            dependencies = manager.dependency_manager.dependencies_for(item)
            self.radius.setText(f"Curve: {getattr(item, 'curve_type', 'Curve')}")
            self.width.setText(
                f"References: {references}  Markers: {len(marker_points)}"
            )
            self.line_type.setText(
                f"Group: {getattr(metadata, 'group', '') or 'Unassigned'}"
            )
            self.line_weight.setText(f"Dependencies: {len(dependencies)}")
        elif getattr(item, "is_reference_geometry", False):
            dependencies = manager.dependency_manager.dependencies_for(item)
            metadata = getattr(item, "metadata", None)
            self.radius.setText(
                f"Reference: {getattr(item, 'reference_type', 'Reference')}"
            )
            self.width.setText(f"Targets: {len(getattr(item, 'target_ids', []))}")
            self.line_type.setText(
                f"Group: {getattr(metadata, 'group', '') or 'Unassigned'}"
            )
            self.line_weight.setText(f"Dependencies: {len(dependencies)}")
        elif getattr(item, "is_construction_reference", False):
            dependencies = manager.dependency_manager.dependencies_for(item)
            metadata = getattr(item, "metadata", None)
            self.radius.setText(
                f"Construction: {getattr(item, 'construction_type', 'Construction')}"
            )
            self.width.setText(f"References: {len(getattr(item, 'reference_ids', []))}")
            self.line_type.setText(
                f"Group: {getattr(metadata, 'group', '') or 'Unassigned'}"
            )
            self.line_weight.setText(
                f"{'Locked' if getattr(item, 'locked', False) else 'Unlocked'}  "
                f"Dependencies: {len(dependencies)}"
            )
        elif getattr(item, "is_assembly", False):
            components = manager.components_for_assembly(item)
            instances = manager.instances_for_assembly(item)
            mates = manager.mates_for_assembly(item)
            exploded_views = manager.exploded_views_for_assembly(item)
            configurations = manager.configurations_for_assembly(item)
            self.radius.setText(
                f"Components: {len(components)}  Instances: {len(instances)}  "
                f"Mates: {len(mates)}"
            )
            self.width.setText(
                f"Exploded Views: {len(exploded_views)}  "
                f"Configurations: {len(configurations)}"
            )
            self.line_type.setText(
                "Active" if getattr(item, "active", False) else "Inactive"
            )
            self.line_weight.setText(
                f"{'Locked' if getattr(item, 'locked', False) else 'Unlocked'}  "
                f"{'Visible' if getattr(item, 'visible', True) else 'Hidden'}"
            )
        elif getattr(item, "is_assembly_component", False):
            instances = [
                instance for instance in getattr(manager, "assembly_instances", []) + getattr(manager, "component_occurrences", [])
                if instance.id in getattr(item, "instance_ids", [])
            ]
            reference = getattr(item, "product_part_id", "") or getattr(item, "subassembly_id", "")
            self.radius.setText(f"Reference: {reference or 'Unassigned'}")
            self.width.setText(f"Instances: {len(instances)}")
            self.line_type.setText(
                "Suppressed" if getattr(item, "suppressed", False) else "Active"
            )
            self.line_weight.setText(
                "Locked" if getattr(item, "locked", False) else "Unlocked"
            )
        elif getattr(item, "is_assembly_instance", False) or getattr(item, "is_component_occurrence", False):
            self.radius.setText(f"Component: {getattr(item, 'component_id', '') or 'Unassigned'}")
            self.width.setText(
                f"Position: {self._number(getattr(location, 'x', 0.0))}, "
                f"{self._number(getattr(location, 'y', 0.0))}, "
                f"{self._number(getattr(location, 'z', 0.0))}"
            )
            self.line_type.setText(
                "Suppressed" if getattr(item, "suppressed", False) else "Active"
            )
            self.line_weight.setText(
                "Locked" if getattr(item, "locked", False) else "Unlocked"
            )
        elif getattr(item, "is_mate", False):
            definition = getattr(item, "definition", None)
            self.radius.setText(f"Mate: {getattr(definition, 'mate_type', 'Mate')}")
            self.width.setText(
                f"A: {getattr(definition, 'entity_a_id', '') or 'Unassigned'}  "
                f"B: {getattr(definition, 'entity_b_id', '') or 'Unassigned'}"
            )
            self.length.setText(
                f"Distance: {self._number(getattr(definition, 'distance', 0.0))}"
            )
            self.angle.setText(
                f"Angle: {self._number(getattr(definition, 'angle', 0.0))}"
            )
            self.line_type.setText(
                "Enabled" if getattr(item, "enabled", True) else "Disabled"
            )
            self.line_weight.setText(
                f"Status: {getattr(getattr(item, 'metadata', None), 'status', 'Stored')}"
            )
        elif getattr(item, "is_exploded_view", False):
            steps = manager.exploded_view_manager.steps_for_view(item)
            self.radius.setText(f"Steps: {len(steps)}")
            self.width.setText(f"Assembly: {getattr(item, 'assembly_id', '') or 'Unassigned'}")
            self.line_type.setText(
                "Active" if getattr(item, "active", False) else "Stored"
            )
            self.line_weight.setText(
                "Visible" if getattr(item, "visible", True) else "Hidden"
            )
        elif getattr(item, "is_assembly_configuration", False):
            self.radius.setText(
                f"Suppression: {len(getattr(item, 'suppression_states', {}))}  "
                f"Visibility: {len(getattr(item, 'visibility_states', {}))}"
            )
            self.width.setText(f"Assembly: {getattr(item, 'assembly_id', '') or 'Unassigned'}")
            self.line_type.setText(
                "Active" if getattr(item, "active", False) else "Inactive"
            )
        elif getattr(item, "is_mechanical_library", False):
            components = manager.mechanical_components_for_library(item)
            self.radius.setText(f"Components: {len(components)}")
            self.width.setText(
                f"Categories: {len(getattr(item, 'category_ids', []))}  "
                f"Families: {len(getattr(item, 'family_ids', []))}"
            )
            self.line_type.setText(f"Standards: {len(getattr(item, 'standard_ids', []))}")
        elif getattr(item, "is_mechanical_category", False):
            self.radius.setText(f"Components: {len(getattr(item, 'component_ids', []))}")
            self.width.setText(f"Families: {len(getattr(item, 'family_ids', []))}")
            self.line_type.setText(f"Library: {getattr(item, 'library_id', '') or 'Unassigned'}")
        elif getattr(item, "is_mechanical_family", False):
            self.radius.setText(f"Components: {len(getattr(item, 'component_ids', []))}")
            self.width.setText(f"Category: {getattr(item, 'category_id', '') or 'Unassigned'}")
            self.line_type.setText(f"Library: {getattr(item, 'library_id', '') or 'Unassigned'}")
        elif getattr(item, "is_mechanical_component", False):
            self.radius.setText(f"Product Part: {getattr(item, 'product_part_id', '') or 'Unassigned'}")
            self.width.setText(f"Family: {getattr(item, 'family_id', '') or 'Unassigned'}")
            self.line_type.setText(f"Standard: {getattr(item, 'standard_id', '') or 'Unassigned'}")
            self.line_weight.setText(f"Category: {getattr(item, 'category_id', '') or 'Unassigned'}")
        elif getattr(item, "is_sheet_metal", False):
            bodies = manager.sheet_metal_bodies_for(item)
            flat_patterns = manager.flat_patterns_for(item)
            self.radius.setText(f"Bodies: {len(bodies)}  Flat Patterns: {len(flat_patterns)}")
            self.width.setText(f"Product Part: {getattr(item, 'product_part_id', '') or 'Unassigned'}")
            self.line_type.setText(f"Rule: {getattr(item, 'rule_id', '') or 'Unassigned'}")
            self.line_weight.setText(
                f"Operation: {getattr(getattr(item, 'metadata', None), 'operation', 'Sheet Metal')}"
            )
        elif getattr(item, "is_sheet_metal_body", False):
            self.radius.setText(f"Sheet Metal Part: {getattr(item, 'sheet_metal_part_id', '') or 'Unassigned'}")
            self.width.setText(f"Mesh: {getattr(item, 'mesh_entity_id', '') or 'Unassigned'}")
            self.line_type.setText(
                f"Operation: {getattr(getattr(item, 'metadata', None), 'operation', 'Sheet Metal')}"
            )
            self.line_weight.setText(f"Source Body: {getattr(item, 'body_id', '') or 'Unassigned'}")
        elif getattr(item, "is_flat_pattern", False):
            self.radius.setText("Flat Pattern: Metadata Only")
            self.width.setText(f"Sheet Metal Part: {getattr(item, 'sheet_metal_part_id', '') or 'Unassigned'}")
            self.line_type.setText(f"Body: {getattr(item, 'body_id', '') or 'Unassigned'}")
        elif getattr(item, "is_sheet_metal_rule", False):
            self.radius.setText(f"Thickness: {self._number(getattr(item, 'thickness', 0.0))}")
            self.width.setText(f"Inside Radius: {self._number(getattr(item, 'inside_radius', 0.0))}")
            self.line_type.setText(
                f"K-Factor: {self._number(getattr(getattr(item, 'k_factor', None), 'value', 0.0))}"
            )
            self.line_weight.setText(f"Material: {getattr(item, 'material_id', '') or 'Unassigned'}")
        elif getattr(item, "is_product_validation_session", False):
            results = manager.validation_results_for(item)
            self.radius.setText(f"Targets: {len(getattr(item, 'target_ids', []))}  Results: {len(results)}")
            self.width.setText(f"Rules: {len(getattr(item, 'rule_ids', []))}")
            self.line_type.setText(f"Status: {getattr(getattr(item, 'metadata', None), 'status', 'Pending')}")
            self.line_weight.setText(f"History: {len(getattr(item, 'history', []))}")
        elif getattr(item, "is_product_validation_rule", False):
            self.radius.setText(f"Rule: {getattr(item, 'rule_type', 'General')}")
            self.width.setText(f"Category: {getattr(item, 'category_id', '') or 'Unassigned'}")
            self.line_type.setText(f"Severity: {getattr(item, 'severity', 'Info')}")
        elif getattr(item, "is_product_validation_result", False):
            self.radius.setText(f"Status: {getattr(item, 'status', 'Stored')}")
            self.width.setText(f"Target: {getattr(item, 'target_id', '') or 'Unassigned'}")
            self.line_type.setText(f"Severity: {getattr(item, 'severity', 'Info')}")
            self.line_weight.setText(f"Rule: {getattr(item, 'rule_id', '') or 'Unassigned'}")
        elif getattr(item, "is_product_analysis", False):
            physical = getattr(item, "physical_properties", None)
            manufacturing = getattr(item, "manufacturing_properties", None)
            self.radius.setText(f"Mass: {self._number(getattr(physical, 'mass', 0.0))}")
            self.width.setText(f"Volume: {self._number(getattr(physical, 'volume', 0.0))}")
            self.height.setText(f"Surface Area: {self._number(getattr(physical, 'surface_area', 0.0))}")
            self.line_type.setText(f"Target: {getattr(item, 'target_id', '') or 'Unassigned'}")
            self.line_weight.setText(f"Material Usage: {len(getattr(manufacturing, 'material_usage', {}))}")
        elif getattr(item, "is_manufacturing_report", False):
            self.radius.setText(f"Rules: {len(getattr(item, 'rule_ids', []))}")
            self.width.setText(f"Issues: {len(getattr(item, 'issue_ids', []))}")
            self.line_type.setText(f"Target: {getattr(item, 'target_id', '') or 'Unassigned'}")
            self.line_weight.setText(f"Process: {getattr(getattr(item, 'metadata', None), 'process', '') or 'Readiness'}")
        elif getattr(item, "is_product_report", False):
            metadata = getattr(item, "metadata", None)
            self.radius.setText(f"Report: {getattr(metadata, 'report_type', 'Summary')}")
            self.width.setText(f"Sources: {len(getattr(item, 'source_ids', []))}")
            self.line_type.setText(f"Format: {getattr(metadata, 'format', 'Internal')}")
            self.line_weight.setText(f"Status: {getattr(metadata, 'status', 'Stored')}")
        elif getattr(item, "is_cam_document", False):
            jobs = manager.cam_jobs_for_document(item)
            self.radius.setText(f"CAM Jobs: {len(jobs)}")
            self.width.setText(f"Active Job: {getattr(item, 'active_job_id', '') or 'Unassigned'}")
            self.line_type.setText("Manufacturing Document")
            self.line_weight.setText("Definition Only")
        elif getattr(item, "is_cam_job", False):
            setups = manager.cam_setups_for_job(item)
            operations = manager.cam_operations_for_job(item)
            self.radius.setText(f"Setups: {len(setups)}  Operations: {len(operations)}")
            self.width.setText(f"Targets: {len(getattr(item, 'target_ids', []))}")
            self.line_type.setText("Active" if getattr(item, "active", False) else "Inactive")
            self.line_weight.setText("Definition Only")
        elif getattr(item, "is_cam_setup", False):
            stock = getattr(item, "stock", None)
            wcs = getattr(item, "work_coordinate_system", None)
            self.radius.setText(f"Stock: {getattr(stock, 'stock_type', 'Box')}")
            self.width.setText(f"Targets: {len(getattr(stock, 'target_ids', []))}")
            self.line_type.setText(f"WCS: {getattr(wcs, 'name', 'WCS')}")
            self.line_weight.setText(f"Material: {getattr(stock, 'material_id', '') or 'Unassigned'}")
        elif getattr(item, "is_cam_operation", False):
            metadata = getattr(item, "metadata", None)
            parameters = getattr(item, "parameters", None)
            if getattr(item, "is_router_operation", False):
                router = getattr(item, "router_metadata", None)
                profile = getattr(item, "router_profile", None)
                props = getattr(parameters, "properties", {})
                self.radius.setText(f"Router: {getattr(item, 'operation_type', 'Profile Cut')}")
                self.width.setText(
                    f"Depth: {self._number(props.get('cut_depth', getattr(parameters, 'depth', 0.0)))}  "
                    f"Step Down: {self._number(getattr(parameters, 'step_down', 0.0))}"
                )
                self.height.setText(
                    f"Step Over: {self._number(getattr(parameters, 'stepover', 0.0))}  "
                    f"Passes: {props.get('pass_count', 1)}"
                )
                self.line_type.setText(
                    f"Tabs: {getattr(getattr(profile, 'tabs', None), 'count', 0)}  "
                    f"Bridges: {getattr(getattr(profile, 'bridges', None), 'count', 0)}"
                )
                self.line_weight.setText(
                    f"{'Enabled' if getattr(metadata, 'enabled', True) else 'Disabled'}  "
                    f"Tool: {getattr(parameters, 'tool_id', '') or 'Unassigned'}"
                )
                self.angle.setText(
                    f"Safe: {self._number(getattr(getattr(profile, 'safe_height', None), 'value', 0.0))}  "
                    f"Clearance: {self._number(getattr(getattr(profile, 'clearance_height', None), 'value', 0.0))}  "
                    f"Fixtures: {len(getattr(router, 'fixture_ids', []))}"
                )
            elif getattr(item, "is_laser_operation", False):
                lp = getattr(item, "laser_plasma_metadata", None)
                props = getattr(parameters, "properties", {})
                self.radius.setText(f"Laser: {getattr(item, 'operation_type', 'Vector Cut')}")
                self.width.setText(
                    f"Power: {self._number(props.get('laser_power', 0.0))}  "
                    f"Speed: {self._number(props.get('cut_speed', 0.0))}"
                )
                self.height.setText(
                    f"Passes: {props.get('pass_count', 1)}  "
                    f"Focus: {self._number(props.get('focus_offset', 0.0))}"
                )
                self.line_type.setText(
                    f"Material: {getattr(lp, 'material_profile_id', '') or 'Unassigned'}  "
                    f"Profile: {getattr(lp, 'cutting_profile_id', '') or 'None'}"
                )
                self.line_weight.setText(
                    f"{'Enabled' if getattr(metadata, 'enabled', True) else 'Disabled'}  "
                    f"Tool: {getattr(parameters, 'tool_id', '') or 'Unassigned'}"
                )
                self.angle.setText(f"Power Profile: {getattr(lp, 'power_profile_id', '') or 'None'}")
            elif getattr(item, "is_plasma_operation", False):
                lp = getattr(item, "laser_plasma_metadata", None)
                props = getattr(parameters, "properties", {})
                self.radius.setText(f"Plasma: {getattr(item, 'operation_type', 'Plasma Cut')}")
                self.width.setText(
                    f"Pierce: {self._number(props.get('pierce_height', 0.0))}  "
                    f"Cut: {self._number(props.get('cut_height', 0.0))}"
                )
                self.height.setText(
                    f"Kerf: {self._number(props.get('kerf_width', 0.0))}  "
                    f"Delay: {self._number(props.get('pierce_delay', 0.0))}"
                )
                self.line_type.setText(
                    f"Material: {getattr(lp, 'material_profile_id', '') or 'Unassigned'}  "
                    f"Gas: {getattr(lp, 'gas_profile_id', '') or 'None'}"
                )
                self.line_weight.setText(
                    f"{'Enabled' if getattr(metadata, 'enabled', True) else 'Disabled'}  "
                    f"Tool: {getattr(parameters, 'tool_id', '') or 'Unassigned'}"
                )
                self.angle.setText(f"Direction: {props.get('cut_direction', 'Climb')}")
            elif getattr(item, "is_three_axis_operation", False):
                strategy = getattr(item, "strategy", None)
                three_axis = getattr(item, "three_axis_metadata", None)
                self.radius.setText(f"3 Axis: {getattr(item, 'operation_type', 'Parallel')}")
                self.width.setText(
                    f"Tolerance: {self._number(getattr(strategy, 'tolerance', 0.0))}  "
                    f"Cusp: {self._number(getattr(strategy, 'maximum_cusp_height', 0.0))}"
                )
                self.height.setText(
                    f"Step Down: {self._number(getattr(strategy, 'stepdown', 0.0))}  "
                    f"Step Over: {self._number(getattr(strategy, 'stepover', 0.0))}"
                )
                self.line_type.setText(
                    f"Boundary: {getattr(strategy, 'boundary_mode', 'Contact')}  "
                    f"Cut: {getattr(strategy, 'cut_direction', 'One Way')}"
                )
                self.line_weight.setText(
                    f"Boundaries: {len(getattr(three_axis, 'boundary_ids', []))}  "
                    f"{'Enabled' if getattr(metadata, 'enabled', True) else 'Disabled'}  "
                    f"Tool: {getattr(strategy, 'tool_id', '') or 'Unassigned'}"
                )
                self.angle.setText(
                    f"Surface: {getattr(three_axis, 'surface_selection_id', '') or 'None'}  "
                    f"Region: {getattr(three_axis, 'machining_region_id', '') or 'None'}"
                )
            else:
                self.radius.setText(f"Operation: {getattr(item, 'operation_type', 'Facing')}")
                self.width.setText(
                    f"Targets: {len(getattr(item, 'target_ids', []))}  "
                    f"Depth: {self._number(getattr(parameters, 'depth', 0.0) or getattr(parameters, 'hole_depth', 0.0))}"
                )
                self.height.setText(
                    f"Step Down: {self._number(getattr(parameters, 'step_down', 0.0))}  "
                    f"Step Over: {self._number(getattr(parameters, 'stepover', 0.0))}"
                )
                self.line_type.setText(
                    f"Setup: {getattr(item, 'setup_id', '') or 'Unassigned'}  "
                    f"Group: {getattr(metadata, 'group', '') or 'None'}"
                )
                self.line_weight.setText(
                    f"Status: {getattr(metadata, 'status', 'Definition Only')}  "
                    f"{'Enabled' if getattr(metadata, 'enabled', True) else 'Disabled'}  "
                    f"Tool: {getattr(parameters, 'tool_id', '') or 'Unassigned'}"
                )
                self.angle.setText(
                    f"Feed/Speed: {getattr(parameters, 'feed_speed_profile_id', '') or 'Unassigned'}  "
                    f"Cycle: {getattr(parameters, 'cycle_type', '') or 'None'}"
                )
        elif getattr(item, "is_machining_region", False):
            self.radius.setText(f"Faces: {len(getattr(item, 'face_ids', []))}")
            self.width.setText(f"Surfaces: {len(getattr(item, 'surface_body_ids', []))}")
            self.height.setText(f"Bodies: {len(getattr(item, 'body_ids', []))}")
            self.line_type.setText("Machining Region")
            self.line_weight.setText(f"Part: {getattr(item, 'part_id', '') or 'Unassigned'}")
        elif getattr(item, "is_surface_selection", False):
            self.radius.setText(f"Faces: {len(getattr(item, 'face_ids', []))}")
            self.width.setText(f"Surfaces: {len(getattr(item, 'surface_body_ids', []))}")
            self.height.setText(f"Meshes: {len(getattr(item, 'mesh_entity_ids', []))}")
            self.line_type.setText("Surface Selection")
            self.line_weight.setText(f"Part: {getattr(item, 'part_id', '') or 'Unassigned'}")
        elif getattr(item, "is_machining_boundary", False):
            metadata = getattr(item, "metadata", None)
            self.radius.setText(f"Boundary: {getattr(item, 'boundary_type', 'Boundary')}")
            self.width.setText(f"Curves: {len(getattr(item, 'curve_ids', []))}")
            self.height.setText(f"References: {len(getattr(item, 'reference_ids', []))}")
            self.line_type.setText(f"Containment: {getattr(metadata, 'containment_mode', 'Inside')}")
            self.line_weight.setText(f"Part: {getattr(item, 'part_id', '') or 'Unassigned'}")
        elif getattr(item, "is_laser_job", False):
            self.radius.setText(f"Laser Job: {len(getattr(item, 'operation_ids', []))} operations")
            self.width.setText(f"CAM Job: {getattr(item, 'cam_job_id', '') or 'Unassigned'}")
            self.line_type.setText("Laser Manufacturing")
            self.line_weight.setText("Definition Only")
        elif getattr(item, "is_plasma_job", False):
            self.radius.setText(f"Plasma Job: {len(getattr(item, 'operation_ids', []))} operations")
            self.width.setText(f"CAM Job: {getattr(item, 'cam_job_id', '') or 'Unassigned'}")
            self.line_type.setText("Plasma Manufacturing")
            self.line_weight.setText("Definition Only")
        elif getattr(item, "is_router_job", False):
            self.radius.setText(f"Router Job: {len(getattr(item, 'operation_ids', []))} operations")
            self.width.setText(f"CAM Job: {getattr(item, 'cam_job_id', '') or 'Unassigned'}")
            self.line_type.setText("CNC Router Manufacturing")
            self.line_weight.setText("Definition Only")
        elif getattr(item, "is_clamp_avoidance_region", False):
            self.radius.setText(f"Clamp Region: {len(getattr(item, 'reference_ids', []))} references")
            self.width.setText("Clamp Avoidance")
            self.line_type.setText("Router Fixture Awareness")
            self.line_weight.setText("Reference Metadata Only")
        elif getattr(item, "is_router_fixture", False):
            self.radius.setText(f"Fixture: {len(getattr(item, 'reference_ids', []))} references")
            self.width.setText("Router Fixture")
            self.line_type.setText("Fixture Reference")
            self.line_weight.setText("Metadata Only")
        elif getattr(item, "is_router_metadata_profile", False):
            self.radius.setText(
                f"Safe: {self._number(getattr(getattr(item, 'safe_height', None), 'value', 0.0))}  "
                f"Clearance: {self._number(getattr(getattr(item, 'clearance_height', None), 'value', 0.0))}"
            )
            self.width.setText(
                f"Tabs: {getattr(getattr(item, 'tabs', None), 'count', 0)}  "
                f"Bridges: {getattr(getattr(item, 'bridges', None), 'count', 0)}"
            )
            self.height.setText(f"Onion Skin: {self._number(getattr(getattr(item, 'onion_skin', None), 'thickness', 0.0))}")
            self.line_type.setText("Router Metadata Profile")
            self.line_weight.setText(f"Dust: {getattr(item, 'dust_collection_id', '') or 'None'}")
        elif getattr(item, "is_dust_collection_profile", False):
            self.radius.setText(f"Profile: {getattr(item, 'name', 'Dust Collection')}")
            self.width.setText("Dust Collection Placeholder")
            self.line_type.setText("Router Metadata")
            self.line_weight.setText("Future machine compatibility")
        elif getattr(item, "is_post_processor", False):
            profiles = manager.post_processor_manager.profiles_for_post_processor(item)
            self.radius.setText(f"Post Processor: {getattr(item, 'name', 'Post Processor')}")
            self.width.setText(f"Profiles: {len(profiles)}  Default: {getattr(item, 'default', False)}")
            self.height.setText(f"Controller: {getattr(item, 'controller_profile_id', '') or 'Unassigned'}")
            self.line_type.setText("Post Processor Metadata")
            self.line_weight.setText("No G-Code generation")
        elif getattr(item, "is_post_processor_profile", False):
            settings = getattr(item, "settings", None)
            validation = getattr(getattr(settings, "validation", None), "status", "Not Run")
            self.radius.setText(f"Profile: {getattr(item, 'name', 'Post Processor Profile')}")
            self.width.setText(f"CAM Job: {getattr(item, 'cam_job_id', '') or 'Unassigned'}")
            self.height.setText(f"Output: {getattr(settings, 'output_configuration_id', '') or 'Unassigned'}")
            self.line_type.setText(f"{'Enabled' if getattr(item, 'enabled', True) else 'Disabled'}  Validation: {validation}")
            self.line_weight.setText("Relationship Metadata Only")
        elif getattr(item, "is_controller_profile", False):
            metadata = getattr(item, "metadata", None)
            self.radius.setText(f"Controller: {getattr(item, 'controller_type', 'GenericGCode')}")
            self.width.setText(f"Units: {getattr(metadata, 'units', 'mm')}  Mode: {getattr(metadata, 'coordinate_mode', 'Absolute')}")
            self.height.setText(f"Arcs: {getattr(metadata, 'arc_support', True)}  Feed: {getattr(metadata, 'feed_mode', 'Units per Minute')}")
            self.line_type.setText(f"Version: {getattr(metadata, 'controller_version', '') or 'Unspecified'}")
            self.line_weight.setText("Machine Controller Metadata")
        elif getattr(item, "is_output_configuration", False):
            metadata = getattr(item, "metadata", None)
            coords = getattr(item, "coordinates", None)
            self.radius.setText(f"Program: {getattr(item, 'program_name', '') or getattr(item, 'name', 'Output')}")
            self.width.setText(f"Units: {getattr(coords, 'units', 'mm')}  Offset: {getattr(coords, 'work_offset', 'G54')}")
            self.height.setText(f"Extension: {getattr(metadata, 'file_extension', '.nc')}")
            self.line_type.setText(f"Comments: {getattr(metadata, 'comment_style', 'Parentheses')}")
            self.line_weight.setText("Output Configuration Metadata")
        elif getattr(item, "is_output_template", False):
            self.radius.setText(f"Template: {getattr(item, 'template_type', 'Generic')}")
            self.width.setText(f"Name: {getattr(item, 'name', 'Output Template')}")
            self.line_type.setText("Output Template")
            self.line_weight.setText("Metadata Only")
        elif getattr(item, "is_machine_library", False):
            machines = manager.machines_for_library(item)
            self.radius.setText(f"Machines: {len(machines)}  Profiles: {len(getattr(item, 'profile_ids', []))}")
            self.width.setText(f"Categories: {len(getattr(item, 'category_ids', []))}  Favorites: {len(getattr(item, 'favorite_machine_ids', []))}")
            self.line_type.setText("Machine Library")
            self.line_weight.setText("Future cloud library ready")
        elif getattr(item, "is_machine_definition", False):
            metadata = getattr(item, "metadata", None)
            capabilities = getattr(item, "capabilities", None)
            envelope = getattr(capabilities, "work_envelope", None)
            travel = getattr(capabilities, "travel_limits", None)
            spindle = getattr(capabilities, "spindle_configuration", None)
            self.radius.setText(f"Machine: {getattr(item, 'machine_type', 'Generic')}")
            self.width.setText(f"Manufacturer: {getattr(metadata, 'manufacturer', '') or 'Unassigned'}  Model: {getattr(metadata, 'model', '') or 'Unassigned'}")
            self.height.setText(
                f"Envelope: {self._number(getattr(envelope, 'width', 0.0))} x "
                f"{self._number(getattr(envelope, 'depth', 0.0))} x "
                f"{self._number(getattr(envelope, 'height', 0.0))}"
            )
            printer = getattr(item, "printer_metadata", None)
            if getattr(item, "is_printer_profile", False):
                self.line_type.setText(
                    f"Printer: nozzle {self._number(getattr(printer, 'nozzle_diameter', 0.0))}  "
                    f"layers {self._number(getattr(printer, 'minimum_layer_height', 0.0))}-"
                    f"{self._number(getattr(printer, 'maximum_layer_height', 0.0))}"
                )
            else:
                self.line_type.setText(f"Controller: {getattr(metadata, 'supported_controller', '') or 'Unassigned'}")
            self.line_weight.setText(
                f"Travel: {self._number(getattr(travel, 'x', 0.0))}/"
                f"{self._number(getattr(travel, 'y', 0.0))}/"
                f"{self._number(getattr(travel, 'z', 0.0))}  "
                f"RPM: {self._number(getattr(spindle, 'maximum_rpm', 0.0))}"
            )
        elif getattr(item, "is_machine_profile", False):
            validation = getattr(item, "validation", None)
            self.radius.setText(f"Profile: {getattr(item, 'name', 'Machine Profile')}")
            self.width.setText(f"CAM Job: {getattr(item, 'cam_job_id', '') or 'Unassigned'}  Setup: {getattr(item, 'setup_id', '') or 'Unassigned'}")
            self.height.setText(f"Machine: {getattr(item, 'machine_id', '') or 'Unassigned'}")
            self.line_type.setText(f"{'Enabled' if getattr(item, 'enabled', True) else 'Disabled'}  Validation: {getattr(validation, 'status', 'Not Run')}")
            self.line_weight.setText("Machine assignment metadata only")
        elif getattr(item, "is_slice_job", False):
            operations = manager.slice_operations_for_job(item)
            self.radius.setText(f"Slice Job: {len(operations)} operations")
            self.width.setText(f"CAM Job: {getattr(item, 'cam_job_id', '') or 'Unassigned'}")
            self.height.setText(f"Profile: {getattr(item, 'profile_id', '') or 'Unassigned'}")
            self.line_type.setText(f"{'Enabled' if getattr(item, 'enabled', True) else 'Disabled'}  {getattr(getattr(item, 'metadata', None), 'status', 'Not Sliced')}")
            self.line_weight.setText("No slicing or G-Code generation")
        elif getattr(item, "is_slice_profile", False):
            print_profile = getattr(item, "print_profile", None)
            layer = getattr(print_profile, "layer", None)
            infill = getattr(print_profile, "infill", None)
            support = getattr(print_profile, "support", None)
            definition = getattr(item, "layer_definition", None)
            self.radius.setText(f"Slice Profile: {getattr(item, 'name', 'Slice Profile')}")
            self.width.setText(
                f"Layer: {self._number(getattr(layer, 'layer_height', 0.0))}  "
                f"Infill: {self._number(getattr(infill, 'percentage', 0.0))}%"
            )
            self.height.setText(f"Layers: {getattr(definition, 'layer_count', 0)}  Support: {getattr(support, 'enabled', False)}")
            self.line_type.setText(f"Machine: {getattr(item, 'machine_profile_id', '') or 'Unassigned'}")
            self.line_weight.setText("Layer metadata only")
        elif getattr(item, "is_slice_operation", False):
            self.radius.setText(f"Slice Operation: {getattr(item, 'name', 'Slice Operation')}")
            self.width.setText(f"Targets: {len(getattr(item, 'target_ids', []))}")
            self.height.setText(f"Profile: {getattr(item, 'profile_id', '') or 'Unassigned'}")
            self.line_type.setText("Additive Operation Metadata")
            self.line_weight.setText("No extrusion paths")
        elif getattr(item, "is_simulation_job", False):
            result = getattr(item, "result", None)
            estimate = getattr(result, "estimate", None)
            self.radius.setText(f"Simulation Job: {getattr(item, 'name', 'Simulation Job')}")
            self.width.setText(f"CAM: {getattr(item, 'cam_job_id', '') or 'None'}  Slice: {getattr(item, 'slice_job_id', '') or 'None'}")
            self.height.setText(f"Runtime: {self._number(getattr(estimate, 'estimated_runtime', 0.0))}")
            self.line_type.setText(f"{'Enabled' if getattr(item, 'enabled', True) else 'Disabled'}  {getattr(result, 'status', 'Not Run')}")
            self.line_weight.setText("Metadata only; no simulation playback")
        elif getattr(item, "is_simulation_profile", False):
            metadata = getattr(item, "metadata", None)
            validation = getattr(item, "validation", None)
            estimate = getattr(item, "estimate", None)
            self.radius.setText(f"Simulation: {getattr(metadata, 'simulation_type', 'Generic')}")
            self.width.setText(f"Mode: {getattr(metadata, 'simulation_mode', 'Preview')}  Quality: {getattr(metadata, 'simulation_quality', 'Standard')}")
            self.height.setText(f"Travel: {self._number(getattr(estimate, 'travel_distance', 0.0))}  Layers: {getattr(estimate, 'layer_count', 0)}")
            self.line_type.setText(f"Ready: {getattr(getattr(validation, 'readiness', None), 'ready', False)}  Warnings: {len(getattr(validation, 'warnings', []))}")
            self.line_weight.setText("Validation hooks only")
        elif getattr(item, "is_nesting_job", False):
            result = getattr(item, "result", None)
            estimate = getattr(result, "estimate", None)
            panels = getattr(getattr(estimate, "panel_statistics", None), "panels", 0)
            self.radius.setText(f"Nesting Job: {getattr(item, 'name', 'Nesting Job')}")
            self.width.setText(f"CAM: {getattr(item, 'cam_job_id', '') or 'Unassigned'}  Profile: {getattr(item, 'profile_id', '') or 'Unassigned'}")
            self.height.setText(f"Estimated Panels: {panels}")
            self.line_type.setText(f"{'Enabled' if getattr(item, 'enabled', True) else 'Disabled'}  {getattr(result, 'status', 'Not Nested')}")
            self.line_weight.setText("Metadata only; no nesting execution")
        elif getattr(item, "is_nesting_profile", False):
            estimate = getattr(item, "estimate", None)
            waste = getattr(getattr(estimate, "waste", None), "percentage", 0.0)
            yield_estimate = getattr(getattr(estimate, "yield_estimate", None), "percentage", 0.0)
            self.radius.setText(f"Stock Profiles: {len(getattr(item, 'stock_profile_ids', []))}")
            self.width.setText(f"Waste: {self._number(waste)}%  Yield: {self._number(yield_estimate)}%")
            self.height.setText(f"Machine: {getattr(item, 'machine_profile_id', '') or 'Unassigned'}")
            self.line_type.setText("Nesting Profile")
            self.line_weight.setText("Future background nesting ready")
        elif getattr(item, "is_stock_library", False):
            self.radius.setText(f"Stock Profiles: {len(getattr(item, 'profile_ids', []))}")
            self.width.setText(f"Type: {getattr(getattr(item, 'metadata', None), 'stock_type', 'Stock Library')}")
            self.line_type.setText("Stock Library")
            self.line_weight.setText("Uses Engineering Material references")
        elif getattr(item, "is_stock_profile", False):
            metadata = getattr(item, "metadata", None)
            material = getattr(item, "material_reference", None)
            self.radius.setText(f"{getattr(metadata, 'stock_type', 'Sheet Stock')}: {getattr(item, 'quantity', 1)}")
            self.width.setText(f"{self._number(getattr(item, 'length', 0.0))} x {self._number(getattr(item, 'width', 0.0))}")
            self.height.setText(f"Thickness: {self._number(getattr(item, 'thickness', 0.0))}")
            self.line_type.setText(f"Material: {getattr(material, 'material_name', '') or getattr(material, 'engineering_material_id', '') or 'Unassigned'}")
            self.line_weight.setText(f"Grain: {getattr(metadata, 'grain_direction', '') or 'None'}")
        elif getattr(item, "is_fabrication_plan", False):
            self.radius.setText(f"Cut Lists: {len(getattr(item, 'cut_list_ids', []))}  Panels: {len(getattr(item, 'panel_layout_ids', []))}")
            self.width.setText(f"Groups: {len(getattr(item, 'group_ids', []))}  Assignments: {len(getattr(item, 'stock_assignment_ids', []))}")
            self.height.setText(f"CAM: {getattr(item, 'cam_job_id', '') or 'Unassigned'}")
            self.line_type.setText("Fabrication Plan")
            self.line_weight.setText("Planning metadata only")
        elif getattr(item, "is_fabrication_job", False):
            self.radius.setText(f"Fabrication Job: {getattr(item, 'name', 'Fabrication Job')}")
            self.width.setText(f"Plan: {getattr(item, 'plan_id', '') or 'Unassigned'}")
            self.height.setText(f"Machine: {getattr(item, 'machine_profile_id', '') or 'Unassigned'}")
            self.line_type.setText("Enabled" if getattr(item, "enabled", True) else "Disabled")
            self.line_weight.setText("No machine execution")
        elif getattr(item, "is_fabrication_group", False):
            self.radius.setText(f"Parts: {len(getattr(item, 'assigned_part_ids', []))}")
            self.width.setText(f"Assignments: {len(getattr(item, 'stock_assignment_ids', []))}")
            self.line_type.setText("Fabrication Group")
            self.line_weight.setText("Relationship metadata only")
        elif getattr(item, "is_cut_list", False):
            self.radius.setText(f"Parts: {len(getattr(item, 'part_ids', []))}")
            self.width.setText(f"Placements: {len(getattr(item, 'placement_ids', []))}")
            self.height.setText(f"Assignments: {len(getattr(item, 'assignment_ids', []))}")
            self.line_type.setText("Cut List")
            self.line_weight.setText("No cutting path generation")
        elif getattr(item, "is_panel_layout", False):
            self.radius.setText(f"Panel: {getattr(item, 'stock_profile_id', '') or 'Unassigned'}")
            self.width.setText(f"Placements: {len(getattr(item, 'placement_ids', []))}")
            self.line_type.setText("Panel Layout")
            self.line_weight.setText("No nesting preview or optimization")
        elif getattr(item, "is_manufacturing_job", False):
            metadata = getattr(item, "metadata", None)
            self.radius.setText(f"Manufacturing Job: {getattr(item, 'name', 'Manufacturing Job')}")
            self.width.setText(f"CAM: {getattr(item, 'cam_job_id', '') or 'None'}  Nesting: {getattr(item, 'nesting_job_id', '') or 'None'}")
            self.height.setText(f"Slice: {getattr(item, 'slice_job_id', '') or 'None'}  Simulation: {getattr(item, 'simulation_job_id', '') or 'None'}")
            self.line_type.setText(f"{'Enabled' if getattr(item, 'enabled', True) else 'Disabled'}  {getattr(metadata, 'status', 'Pending')}")
            self.line_weight.setText(f"Priority: {getattr(metadata, 'priority', 'Normal')}  Group: {getattr(metadata, 'group', '') or 'None'}")
        elif getattr(item, "is_manufacturing_job_collection", False):
            self.radius.setText(f"Jobs: {len(getattr(item, 'job_ids', []))}")
            self.line_type.setText("Manufacturing Job Collection")
            self.line_weight.setText("Grouping metadata only")
        elif getattr(item, "is_manufacturing_job_profile", False):
            self.radius.setText(f"References: {len(getattr(item, 'reference_ids', []))}")
            self.line_type.setText("Manufacturing Job Profile")
            self.line_weight.setText("Future background processing ready")
        elif getattr(item, "is_manufacturing_validation_profile", False):
            self.radius.setText(f"Validation Profile: {getattr(item, 'name', 'Validation Profile')}")
            self.width.setText(f"References: {len(getattr(item, 'reference_ids', []))}")
            self.line_type.setText(f"Status: {getattr(getattr(item, 'metadata', None), 'status', 'Not Checked')}")
            self.line_weight.setText("Metadata only; no validation algorithms")
        elif getattr(item, "is_manufacturing_validation_result", False):
            self.radius.setText(f"Validation Result: {getattr(item, 'readiness', 'Not Checked')}")
            self.width.setText(f"Profile: {getattr(item, 'profile_id', '') or 'Unassigned'}")
            self.height.setText(f"Job: {getattr(item, 'job_id', '') or 'Unassigned'}")
            self.line_type.setText(f"Issues: {len(getattr(item, 'issues', []))}")
            self.line_weight.setText("Production readiness metadata only")
        elif getattr(item, "is_setup_sheet", False):
            summary = getattr(item, "operation_summary", None)
            self.radius.setText(f"Setup Sheet: {getattr(item, 'name', 'Setup Sheet')}")
            self.width.setText(f"Setup: {getattr(item, 'setup_id', '') or 'Unassigned'}  Job: {getattr(item, 'manufacturing_job_id', '') or 'Unassigned'}")
            self.height.setText(f"Operations: {len(getattr(summary, 'operation_ids', []))}")
            self.line_type.setText(f"Instructions: {len(getattr(item, 'instructions', []))}")
            self.line_weight.setText("Shop-floor document metadata only")
        elif getattr(item, "is_setup_sheet_collection", False):
            self.radius.setText(f"Setup Sheets: {len(getattr(item, 'setup_sheet_ids', []))}")
            self.line_type.setText("Setup Sheet Collection")
            self.line_weight.setText("Documentation grouping metadata")
        elif getattr(item, "is_manufacturing_dashboard", False):
            metrics = getattr(item, "metrics", None)
            self.radius.setText(f"Dashboard Jobs: {len(getattr(item, 'job_ids', []))}")
            self.width.setText(f"Ready: {getattr(metrics, 'ready_jobs', 0)}  Pending: {getattr(metrics, 'pending_jobs', 0)}")
            self.height.setText(f"Warnings: {getattr(metrics, 'warning_jobs', 0)}  Completed: {getattr(metrics, 'completed_jobs', 0)}")
            self.line_type.setText("Manufacturing Dashboard")
            self.line_weight.setText("Dashboard metadata only")
        elif getattr(item, "is_manufacturing_browser", False):
            self.radius.setText("Manufacturing Browser")
            self.line_type.setText("Browser state metadata")
            self.line_weight.setText("No duplicate workspace")
        elif getattr(item, "is_production_queue", False) or getattr(item, "is_job_queue", False):
            self.radius.setText(getattr(item, "name", "Production Queue"))
            self.line_type.setText("Queue metadata")
            self.line_weight.setText("No workflow execution")
        elif getattr(item, "is_job_history", False):
            self.radius.setText("Job History")
            self.line_type.setText("History metadata")
            self.line_weight.setText("No production playback")
        elif getattr(item, "is_parametric_engine", False):
            state = getattr(item, "state", None)
            flags = getattr(state, "flags", None)
            self.radius.setText(f"Documents: {len(getattr(item, 'document_ids', []))}  Sessions: {len(getattr(item, 'session_ids', []))}")
            self.width.setText(f"State: {getattr(state, 'state', 'Ready')}")
            self.height.setText(f"Ready: {getattr(flags, 'ready', True)}  Dirty: {getattr(flags, 'dirty', False)}")
            self.line_type.setText("Parametric Engine metadata only")
            self.line_weight.setText("No solver, node graph or geometry generation")
        elif getattr(item, "is_parametric_document", False):
            context = getattr(item, "context", None)
            self.radius.setText(f"Sessions: {len(getattr(item, 'session_ids', []))}  References: {len(getattr(item, 'reference_ids', []))}")
            self.width.setText(f"Product Part: {getattr(context, 'product_part_id', '') or 'Unassigned'}")
            self.height.setText(f"Assembly: {getattr(context, 'assembly_id', '') or 'Unassigned'}")
            self.line_type.setText("Parametric Document")
            self.line_weight.setText("Relationship storage only")
        elif getattr(item, "is_parametric_workspace", False):
            self.radius.setText("Parametric Workspace metadata")
            self.width.setText(f"Document: {getattr(item, 'document_id', '') or 'Unassigned'}")
            self.height.setText(f"Contexts: {len(getattr(item, 'context_ids', []))}")
            self.line_type.setText("No duplicate Workspace")
            self.line_weight.setText("Design workspace integration metadata")
        elif getattr(item, "is_parametric_session", False):
            session_state = getattr(item, "session_state", None)
            evaluation = getattr(item, "evaluation_state", None)
            dirty = getattr(item, "dirty_state", None)
            freeze = getattr(item, "freeze_state", None)
            self.radius.setText(f"Session: {getattr(session_state, 'state', 'Ready')}")
            self.width.setText(f"Evaluation: {getattr(evaluation, 'status', 'Not Evaluated')}")
            self.height.setText(f"Dirty: {getattr(dirty, 'dirty', False)}  Frozen: {getattr(freeze, 'frozen', False)}")
            self.line_type.setText(f"References: {len(getattr(item, 'reference_ids', []))}")
            self.line_weight.setText("Future solving placeholder only")
        elif getattr(item, "is_live_solver", False):
            state = getattr(item, "state", None)
            flags = getattr(item, "flags", None)
            queue = getattr(item, "queue", None)
            self.radius.setText(f"Solver: {getattr(item, 'name', 'Live Solver')}")
            self.width.setText(f"State: {getattr(state, 'state', 'Ready')}  Evaluation: {getattr(state, 'evaluation_state', 'Waiting')}")
            self.height.setText(f"Queued: {len(getattr(queue, 'evaluation_queue', []))}  Dirty: {getattr(flags, 'dirty', False)}")
            self.line_type.setText("Live Solver metadata only")
            self.line_weight.setText("No solving or geometry regeneration")
        elif getattr(item, "is_solver_session", False):
            state = getattr(item, "state", None)
            queue = getattr(item, "queue", None)
            self.radius.setText(f"Solver Session: {getattr(item, 'name', 'Solver Session')}")
            self.width.setText(f"State: {getattr(state, 'state', 'Ready')}  Eval: {getattr(state, 'evaluation_state', 'Waiting')}")
            self.height.setText(f"Requests: {len(getattr(item, 'evaluation_request_ids', []))}  Queue: {len(getattr(queue, 'evaluation_queue', []))}")
            self.line_type.setText(f"Parametric Session: {getattr(item, 'parametric_session_id', '') or 'Unassigned'}")
            self.line_weight.setText("Metadata scheduling only")
        elif getattr(item, "is_evaluation_request", False):
            context = getattr(item, "context", None)
            flags = getattr(item, "flags", None)
            self.radius.setText(f"Request: {getattr(item, 'change_type', 'Parameter Changed')}")
            self.width.setText(f"State: {getattr(item, 'state', 'Queued')}  Target: {getattr(item, 'target_id', '') or 'Unassigned'}")
            self.height.setText(f"Objects: {len(getattr(context, 'affected_object_ids', []))}  Parameters: {len(getattr(context, 'affected_parameter_ids', []))}")
            self.line_type.setText(f"Queued: {getattr(flags, 'queued', False)}  Pending: {getattr(flags, 'pending', False)}")
            self.line_weight.setText("No evaluation execution")
        elif getattr(item, "is_evaluation_batch", False):
            self.radius.setText(f"Batch: {getattr(item, 'name', 'Evaluation Batch')}")
            self.width.setText(f"State: {getattr(item, 'state', 'Queued')}")
            self.height.setText(f"Requests: {len(getattr(item, 'request_ids', []))}")
            self.line_type.setText("Batch request metadata")
            self.line_weight.setText("No scheduling algorithm")
        elif getattr(item, "is_evaluation_result", False):
            self.radius.setText(f"Result: {getattr(item, 'state', 'Pending')}")
            self.width.setText(f"Request: {getattr(item, 'request_id', '') or 'Unassigned'}")
            self.height.setText(f"Affected: {len(getattr(item, 'affected_object_ids', []))}")
            self.line_type.setText(getattr(item, "message", "") or "Evaluation result metadata")
            self.line_weight.setText("No computed values")
        elif getattr(item, "is_visual_node_graph", False):
            flags = getattr(item, "flags", None)
            self.radius.setText(f"Graph: {getattr(item, 'name', 'Visual Node Graph')}")
            self.width.setText(f"Nodes: {len(getattr(item, 'node_ids', []))}  Connections: {len(getattr(item, 'connection_ids', []))}")
            self.height.setText(f"Documents: {len(getattr(item, 'document_ids', []))}  Sessions: {len(getattr(item, 'session_ids', []))}")
            self.line_type.setText(f"Validation: {getattr(flags, 'validation_status', 'Not Checked')}")
            self.line_weight.setText("Metadata only; no node execution")
        elif getattr(item, "is_visual_node_graph_document", False) or getattr(item, "is_visual_node_graph_workspace", False) or getattr(item, "is_visual_node_graph_session", False):
            self.radius.setText(getattr(item, "name", "Node Graph Record"))
            self.width.setText(f"Graph: {getattr(item, 'graph_id', '') or 'Unassigned'}")
            self.height.setText(f"References: {len(getattr(item, 'reference_ids', []))}")
            self.line_type.setText(getattr(item, "type_name", "NodeGraphRecord"))
            self.line_weight.setText("No duplicate workspace")
        elif getattr(item, "is_visual_node", False):
            flags = getattr(item, "flags", None)
            self.radius.setText(f"Node: {getattr(item, 'display_name', getattr(item, 'name', 'Visual Node'))}")
            self.width.setText(f"Inputs: {len(getattr(item, 'input_port_ids', []))}  Outputs: {len(getattr(item, 'output_port_ids', []))}")
            self.height.setText(f"Connections: {len(getattr(item, 'connection_ids', []))}")
            self.line_type.setText(f"Validation: {getattr(flags, 'validation_status', 'Not Checked')}")
            self.line_weight.setText("Node definition metadata only")
        elif getattr(item, "is_visual_node_port", False):
            self.radius.setText(f"Port: {getattr(item, 'name', 'Port')}")
            self.width.setText(f"Direction: {getattr(item, 'direction', 'Input')}  Type: {getattr(item, 'port_type', 'Any')}")
            self.height.setText(f"Connections: {len(getattr(item, 'connection_ids', []))}")
            self.line_type.setText(f"Capacity: {getattr(item, 'capacity', 'Single')}  Visibility: {getattr(item, 'visibility', 'Visible')}")
            self.line_weight.setText("No data transfer")
        elif getattr(item, "is_node_connection", False):
            metadata = getattr(item, "metadata", None)
            self.radius.setText(f"Connection: {getattr(item, 'name', 'Node Connection')}")
            self.width.setText(f"Source: {getattr(item, 'source_node_id', '') or 'Unassigned'}")
            self.height.setText(f"Destination: {getattr(item, 'destination_node_id', '') or 'Unassigned'}")
            self.line_type.setText(f"Validation: {getattr(metadata, 'validation_status', 'Not Checked')}")
            self.line_weight.setText("No execution or data transfer")
        elif getattr(item, "is_visual_node_graph_item", False):
            self.radius.setText(f"{getattr(item, 'item_type', 'Group')}: {getattr(item, 'name', 'Graph Item')}")
            self.width.setText(f"Nodes: {len(getattr(item, 'node_ids', []))}")
            self.height.setText(f"Connections: {len(getattr(item, 'connection_ids', []))}")
            self.line_type.setText("Graph organization metadata")
            self.line_weight.setText("No UI editor")
        elif getattr(item, "is_data_tree", False):
            flags = getattr(item, "flags", None)
            self.radius.setText(f"Data Tree: {getattr(item, 'name', 'Data Tree')}")
            self.width.setText(f"Branches: {len(getattr(item, 'branch_ids', []))}  Items: {len(getattr(item, 'item_ids', []))}")
            self.height.setText(f"Flows: {len(getattr(item, 'flow_ids', []))}  Graph: {getattr(item, 'graph_id', '') or 'Unassigned'}")
            self.line_type.setText(f"Validation: {getattr(flags, 'validation_status', 'Not Checked')}")
            self.line_weight.setText("Metadata only; no data transfer")
        elif getattr(item, "is_data_branch", False):
            state = getattr(item, "state", None)
            self.radius.setText(f"Branch: {getattr(item, 'branch_identifier', getattr(item, 'name', 'Data Branch'))}")
            self.width.setText(f"Depth: {getattr(item, 'depth', 0)}  Index: {getattr(item, 'index', 0)}")
            self.height.setText(f"Children: {len(getattr(item, 'child_branch_ids', []))}  Items: {len(getattr(item, 'item_ids', []))}")
            self.line_type.setText(f"State: {getattr(state, 'state', 'Ready')}")
            self.line_weight.setText("Branch metadata only")
        elif getattr(item, "is_data_path", False):
            self.radius.setText(f"Path: {getattr(item, 'name', 'Data Path')}")
            self.width.setText(f"Tree: {getattr(item, 'tree_id', '') or 'Unassigned'}")
            self.height.setText(f"Segments: {len(getattr(item, 'path_segments', []))}  Items: {len(getattr(item, 'item_ids', []))}")
            self.line_type.setText("Data path metadata")
            self.line_weight.setText("No traversal")
        elif getattr(item, "is_data_item", False):
            self.radius.setText(f"Data Item: {getattr(item, 'data_identifier', getattr(item, 'name', 'Data Item'))}")
            self.width.setText(f"Type: {getattr(item, 'data_type', 'Any')}  Parameter: {getattr(item, 'parameter_id', '') or 'None'}")
            self.height.setText(f"Source Node: {getattr(item, 'source_node_id', '') or 'None'}  Destination Node: {getattr(item, 'destination_node_id', '') or 'None'}")
            self.line_type.setText(f"Object: {getattr(item, 'object_id', '') or 'Reference only'}")
            self.line_weight.setText("No object duplication")
        elif getattr(item, "is_data_container", False):
            self.radius.setText(f"Container: {getattr(item, 'name', 'Data Container')}")
            self.width.setText(f"Items: {len(getattr(item, 'item_ids', []))}")
            self.height.setText(f"Flows: {len(getattr(item, 'flow_ids', []))}")
            self.line_type.setText("Data container metadata")
            self.line_weight.setText("No transfer")
        elif getattr(item, "is_data_flow", False):
            flags = getattr(item, "flags", None)
            self.radius.setText(f"Flow: {getattr(item, 'flow_identifier', getattr(item, 'name', 'Data Flow'))}")
            self.width.setText(f"Source: {getattr(item, 'source_id', '') or 'Unassigned'}")
            self.height.setText(f"Destination: {getattr(item, 'destination_id', '') or 'Unassigned'}")
            self.line_type.setText(f"Direction: {getattr(item, 'direction', 'Forward')}  Validation: {getattr(flags, 'validation_status', 'Not Checked')}")
            self.line_weight.setText("No data transfer or execution")
        elif getattr(item, "is_cad_node_library", False):
            self.radius.setText(f"CAD Node Library: {getattr(item, 'name', 'CAD Node Library')}")
            self.width.setText(f"Categories: {len(getattr(item, 'category_ids', []))}  Definitions: {len(getattr(item, 'definition_ids', []))}")
            self.height.setText(f"Templates: {len(getattr(item, 'template_ids', []))}  Graph: {getattr(item, 'graph_id', '') or 'Unassigned'}")
            self.line_type.setText("ParametricEngine subsystem")
            self.line_weight.setText("No CADNodeManager")
        elif getattr(item, "is_cad_node_category", False):
            self.radius.setText(f"CAD Category: {getattr(item, 'name', 'CAD Node Category')}")
            self.width.setText(f"Type: {getattr(item, 'category_type', 'General')}")
            self.height.setText(f"Definitions: {len(getattr(item, 'definition_ids', []))}")
            self.line_type.setText("CAD node category metadata")
            self.line_weight.setText("No execution")
        elif getattr(item, "is_cad_node_definition", False):
            metadata = getattr(item, "metadata", None)
            flags = getattr(item, "flags", None)
            self.radius.setText(f"CAD Node: {getattr(item, 'display_name', getattr(item, 'name', 'CAD Node'))}")
            self.width.setText(f"Kind: {getattr(item, 'node_kind', 'General')}  Operation: {getattr(item, 'operation_type', 'Metadata')}")
            self.height.setText(f"Inputs: {len(getattr(item, 'input_port_ids', []))}  Outputs: {len(getattr(item, 'output_port_ids', []))}")
            self.line_type.setText(f"Validation: {getattr(flags, 'validation_status', 'Not Checked')}  Execution: {getattr(metadata, 'execution_status', 'Not Executed')}")
            self.line_weight.setText("Metadata only; no geometry generation")
        elif getattr(item, "is_cad_node_template", False):
            self.radius.setText(f"CAD Template: {getattr(item, 'name', 'CAD Node Template')}")
            self.width.setText(f"Library: {getattr(item, 'library_id', '') or 'Unassigned'}")
            self.height.setText(f"Definition: {getattr(item, 'definition_id', '') or 'Unassigned'}")
            self.line_type.setText("CAD node template metadata")
            self.line_weight.setText("No feature execution")
        elif getattr(item, "is_bim_node_library", False):
            self.radius.setText(f"BIM Node Library: {getattr(item, 'name', 'BIM Node Library')}")
            self.width.setText(f"Categories: {len(getattr(item, 'category_ids', []))}  Definitions: {len(getattr(item, 'definition_ids', []))}")
            self.height.setText(f"Templates: {len(getattr(item, 'template_ids', []))}  CAD Library: {getattr(item, 'cad_node_library_id', '') or 'Unassigned'}")
            self.line_type.setText("ParametricEngine subsystem")
            self.line_weight.setText("No BIMNodeManager")
        elif getattr(item, "is_bim_node_category", False):
            self.radius.setText(f"BIM Category: {getattr(item, 'name', 'BIM Node Category')}")
            self.width.setText(f"Type: {getattr(item, 'category_type', 'General')}")
            self.height.setText(f"Discipline: {getattr(item, 'discipline', '') or 'Unassigned'}  Definitions: {len(getattr(item, 'definition_ids', []))}")
            self.line_type.setText("BIM node category metadata")
            self.line_weight.setText("No BIM generation")
        elif getattr(item, "is_bim_node_definition", False):
            metadata = getattr(item, "metadata", None)
            flags = getattr(item, "flags", None)
            self.radius.setText(f"BIM Node: {getattr(item, 'display_name', getattr(item, 'name', 'BIM Node'))}")
            self.width.setText(f"Kind: {getattr(item, 'node_kind', 'General')}  Operation: {getattr(item, 'operation_type', 'Metadata')}")
            self.height.setText(f"Data Trees: {len(getattr(item, 'data_tree_ids', []))}  CAD Nodes: {len(getattr(item, 'cad_node_ids', []))}")
            self.line_type.setText(f"Validation: {getattr(flags, 'validation_status', 'Not Checked')}  Execution: {getattr(metadata, 'execution_status', 'Not Executed')}")
            self.line_weight.setText("Metadata only; no BIM or geometry generation")
        elif getattr(item, "is_bim_node_template", False):
            self.radius.setText(f"BIM Template: {getattr(item, 'name', 'BIM Node Template')}")
            self.width.setText(f"Library: {getattr(item, 'library_id', '') or 'Unassigned'}")
            self.height.setText(f"Definition: {getattr(item, 'definition_id', '') or 'Unassigned'}")
            self.line_type.setText("BIM node template metadata")
            self.line_weight.setText("No documentation or quantity generation")
        elif getattr(item, "is_manufacturing_node_library", False):
            self.radius.setText(f"Manufacturing Node Library: {getattr(item, 'name', 'Manufacturing Node Library')}")
            self.width.setText(f"Categories: {len(getattr(item, 'category_ids', []))}  Definitions: {len(getattr(item, 'definition_ids', []))}")
            self.height.setText(f"Templates: {len(getattr(item, 'template_ids', []))}  CAD/BIM: {getattr(item, 'cad_node_library_id', '') or 'Unassigned'} / {getattr(item, 'bim_node_library_id', '') or 'Unassigned'}")
            self.line_type.setText("ParametricEngine subsystem")
            self.line_weight.setText("No ManufacturingNodeManager")
        elif getattr(item, "is_manufacturing_node_category", False):
            self.radius.setText(f"Manufacturing Category: {getattr(item, 'name', 'Manufacturing Node Category')}")
            self.width.setText(f"Type: {getattr(item, 'category_type', 'General')}")
            self.height.setText(f"Process: {getattr(item, 'process', '') or 'Unassigned'}  Definitions: {len(getattr(item, 'definition_ids', []))}")
            self.line_type.setText("Manufacturing node category metadata")
            self.line_weight.setText("No manufacturing execution")
        elif getattr(item, "is_manufacturing_node_definition", False):
            metadata = getattr(item, "metadata", None)
            flags = getattr(item, "flags", None)
            self.radius.setText(f"Manufacturing Node: {getattr(item, 'display_name', getattr(item, 'name', 'Manufacturing Node'))}")
            self.width.setText(f"Kind: {getattr(item, 'node_kind', 'General')}  Operation: {getattr(item, 'operation_type', 'Metadata')}")
            self.height.setText(f"Data Trees: {len(getattr(item, 'data_tree_ids', []))}  CAD/BIM Nodes: {len(getattr(item, 'cad_node_ids', []))}/{len(getattr(item, 'bim_node_ids', []))}")
            self.line_type.setText(f"Validation: {getattr(flags, 'validation_status', 'Not Checked')}  Execution: {getattr(metadata, 'execution_status', 'Not Executed')}")
            self.line_weight.setText("Metadata only; no toolpaths, G-Code, simulation, or geometry")
        elif getattr(item, "is_manufacturing_node_template", False):
            self.radius.setText(f"Manufacturing Template: {getattr(item, 'name', 'Manufacturing Node Template')}")
            self.width.setText(f"Library: {getattr(item, 'library_id', '') or 'Unassigned'}")
            self.height.setText(f"Definition: {getattr(item, 'definition_id', '') or 'Unassigned'}")
            self.line_type.setText("Manufacturing node template metadata")
            self.line_weight.setText("No machine, toolpath, or G-Code execution")
        elif getattr(item, "is_ai_node_library", False):
            self.radius.setText(f"AI Node Library: {getattr(item, 'name', 'AI Node Library')}")
            self.width.setText(f"Categories: {len(getattr(item, 'category_ids', []))}  Definitions: {len(getattr(item, 'definition_ids', []))}")
            self.height.setText(f"Manufacturing Library: {getattr(item, 'manufacturing_node_library_id', '') or 'Unassigned'}")
            self.line_type.setText("ParametricEngine subsystem")
            self.line_weight.setText("No AINodeManager")
        elif getattr(item, "is_ai_node_category", False):
            self.radius.setText(f"AI Category: {getattr(item, 'name', 'AI Node Category')}")
            self.width.setText(f"Type: {getattr(item, 'category_type', 'General')}")
            self.height.setText(f"Subcategory: {getattr(item, 'subcategory', '') or 'Unassigned'}  Definitions: {len(getattr(item, 'definition_ids', []))}")
            self.line_type.setText("AI node category metadata")
            self.line_weight.setText("No AI execution")
        elif getattr(item, "is_ai_node_definition", False):
            metadata = getattr(item, "metadata", None)
            flags = getattr(item, "flags", None)
            self.radius.setText(f"AI Node: {getattr(item, 'display_name', getattr(item, 'name', 'AI Node'))}")
            self.width.setText(f"Kind: {getattr(item, 'node_kind', 'AI')}  Operation: {getattr(item, 'operation_type', 'Metadata')}")
            self.height.setText(f"Provider: {getattr(metadata, 'model_provider', '') or 'Placeholder'}  Backend: {getattr(metadata, 'execution_backend', '') or 'Placeholder'}")
            self.line_type.setText(f"Validation: {getattr(flags, 'validation_status', 'Not Checked')}  Execution: {getattr(metadata, 'execution_status', 'Not Executed')}")
            self.line_weight.setText("Metadata only; no AI, API, graph, solver, or geometry execution")
        elif getattr(item, "is_ai_node_template", False):
            self.radius.setText(f"AI Template: {getattr(item, 'name', 'AI Node Template')}")
            self.width.setText(f"Library: {getattr(item, 'library_id', '') or 'Unassigned'}")
            self.height.setText(f"Definition: {getattr(item, 'definition_id', '') or 'Unassigned'}")
            self.line_type.setText("AI node template metadata")
            self.line_weight.setText("No model execution")
        elif getattr(item, "is_script_node_library", False):
            self.radius.setText(f"Script Node Library: {getattr(item, 'name', 'Script Node Library')}")
            self.width.setText(f"Categories: {len(getattr(item, 'category_ids', []))}  Definitions: {len(getattr(item, 'definition_ids', []))}")
            self.height.setText(f"AI Library: {getattr(item, 'ai_node_library_id', '') or 'Unassigned'}")
            self.line_type.setText("ParametricEngine subsystem")
            self.line_weight.setText("No ScriptNodeManager")
        elif getattr(item, "is_script_node_category", False):
            self.radius.setText(f"Script Category: {getattr(item, 'name', 'Script Node Category')}")
            self.width.setText(f"Type: {getattr(item, 'category_type', 'General')}")
            self.height.setText(f"Subcategory: {getattr(item, 'subcategory', '') or 'Unassigned'}  Definitions: {len(getattr(item, 'definition_ids', []))}")
            self.line_type.setText("Script node category metadata")
            self.line_weight.setText("No script execution")
        elif getattr(item, "is_script_node_definition", False):
            metadata = getattr(item, "metadata", None)
            flags = getattr(item, "flags", None)
            self.radius.setText(f"Script Node: {getattr(item, 'display_name', getattr(item, 'name', 'Script Node'))}")
            self.width.setText(f"Kind: {getattr(item, 'node_kind', 'Script')}  Operation: {getattr(item, 'operation_type', 'Metadata')}")
            self.height.setText(f"Language: {getattr(metadata, 'language', '') or 'Placeholder'}  Backend: {getattr(metadata, 'execution_backend', '') or 'Placeholder'}")
            self.line_type.setText(f"Validation: {getattr(flags, 'validation_status', 'Not Checked')}  Execution: {getattr(metadata, 'execution_status', 'Not Executed')}")
            self.line_weight.setText("Metadata only; no script, API, workflow, graph, solver, or geometry execution")
        elif getattr(item, "is_script_node_template", False):
            self.radius.setText(f"Script Template: {getattr(item, 'name', 'Script Node Template')}")
            self.width.setText(f"Library: {getattr(item, 'library_id', '') or 'Unassigned'}")
            self.height.setText(f"Definition: {getattr(item, 'definition_id', '') or 'Unassigned'}")
            self.line_type.setText("Script node template metadata")
            self.line_weight.setText("No runtime execution")
        elif getattr(item, "is_preview_session", False):
            state = getattr(item, "state", None)
            flags = getattr(item, "flags", None)
            self.radius.setText(f"Preview Session: {getattr(item, 'name', 'Preview Session')}")
            self.width.setText(f"Requests: {len(getattr(item, 'request_ids', []))}  Templates: {len(getattr(item, 'template_ids', []))}")
            self.height.setText(f"State: {getattr(state, 'state', 'Idle')}  Dirty: {getattr(state, 'dirty_state', 'Clean')}")
            self.line_type.setText(f"Queued: {getattr(flags, 'queued', False)}  Execution: {getattr(flags, 'execution_status', 'Not Executed')}")
            self.line_weight.setText("Metadata only; no preview generation")
        elif getattr(item, "is_preview_request", False):
            state = getattr(item, "state", None)
            flags = getattr(item, "flags", None)
            self.radius.setText(f"Preview Request: {getattr(item, 'name', 'Preview Request')}")
            self.width.setText(f"Type: {getattr(item, 'request_type', 'Refresh')}")
            self.height.setText(f"State: {getattr(state, 'state', 'Queued')}  Refresh: {getattr(state, 'refresh_state', 'Requested')}")
            self.line_type.setText(f"Dirty: {getattr(flags, 'dirty', False)}  Queued: {getattr(flags, 'queued', False)}")
            self.line_weight.setText("No viewport refresh execution")
        elif getattr(item, "is_preview_template", False):
            self.radius.setText(f"Preview Template: {getattr(item, 'name', 'Preview Template')}")
            self.width.setText(f"Session: {getattr(item, 'session_id', '') or 'Unassigned'}")
            self.height.setText("Template metadata")
            self.line_type.setText("Future preview configuration")
            self.line_weight.setText("No preview rendering")
        elif getattr(item, "is_workspace_synchronization", False):
            metadata = getattr(item, "metadata", None)
            self.radius.setText(f"Workspace Sync: {getattr(item, 'name', 'Workspace Synchronization')}")
            self.width.setText(f"Workspace: {getattr(metadata, 'workspace_state', 'Ready')}  Project: {getattr(metadata, 'project_state', 'Ready')}")
            self.height.setText(f"Selection: {getattr(metadata, 'selection_state', 'Clean')}  Preview: {getattr(metadata, 'preview_state', 'Idle')}")
            self.line_type.setText("Workspace/document/project synchronization metadata")
            self.line_weight.setText("No synchronization execution")
        elif getattr(item, "is_viewport_synchronization", False):
            metadata = getattr(item, "metadata", None)
            self.radius.setText(f"Viewport Sync: {getattr(item, 'name', 'Viewport Synchronization')}")
            self.width.setText(f"Refresh Requested: {getattr(metadata, 'refresh_requested', False)}  Dirty: {getattr(metadata, 'viewport_dirty', False)}")
            self.height.setText(f"View: {getattr(metadata, 'view_synchronization', 'Clean')}  Camera: {getattr(metadata, 'camera_synchronization', 'Clean')}")
            self.line_type.setText("Renderer synchronization metadata")
            self.line_weight.setText("Renderer remains read-only; no refresh execution")
        elif getattr(item, "is_property_synchronization", False):
            metadata = getattr(item, "metadata", None)
            self.radius.setText(f"Property Sync: {getattr(item, 'name', 'Property Synchronization')}")
            self.width.setText(f"Target: {getattr(metadata, 'target_type', 'Workspace')}  IDs: {len(getattr(metadata, 'target_ids', []))}")
            self.height.setText(f"Groups: {len(getattr(metadata, 'synchronized_groups', []))}  State: {getattr(metadata, 'property_state', 'Clean')}")
            self.line_type.setText("Property metadata synchronization")
            self.line_weight.setText("No property mutation")
        elif getattr(item, "is_update_coordination", False):
            metadata = getattr(item, "metadata", None)
            flags = getattr(item, "flags", None)
            self.radius.setText(f"Update Coordination: {getattr(item, 'name', 'Update Coordination')}")
            self.width.setText(f"Request: {getattr(metadata, 'request_type', 'Refresh')}  Target: {getattr(metadata, 'target_id', '') or 'Unassigned'}")
            self.height.setText(f"Dirty: {getattr(metadata, 'dirty_state', 'Dirty')}  Refresh: {getattr(metadata, 'refresh_requested', False)}")
            self.line_type.setText(f"Queued: {getattr(flags, 'queued', False)}")
            self.line_weight.setText("Metadata only; no updates executed")
        elif getattr(item, "is_execution_engine", False):
            flags = getattr(item, "flags", None)
            cache = getattr(item, "cache", None)
            self.radius.setText(f"Execution Engine: {getattr(item, 'name', 'Execution Engine')}")
            self.width.setText(f"Requests: {len(getattr(item, 'request_ids', []))}  Sessions: {len(getattr(item, 'session_ids', []))}")
            self.height.setText(f"Cache: {len(getattr(cache, 'values', {}))}  Pipelines: {len(getattr(item, 'pipeline_ids', []))}")
            self.line_type.setText(f"Queued: {getattr(flags, 'queued', False)}  Running: {getattr(flags, 'running', False)}")
            self.line_weight.setText("ParametricEngine subsystem; no ExecutionManager")
        elif getattr(item, "is_sketch_solver", False):
            state = getattr(item, "state", None)
            diagnostics = getattr(item, "diagnostics", None)
            cache = getattr(item, "cache", None)
            self.radius.setText(f"Sketch Solver: {getattr(item, 'name', 'Sketch Solver')}")
            self.width.setText(f"State: {getattr(state, 'state', 'Ready')}  DOF: {getattr(state, 'dof_state', 'Under Constrained')}")
            self.height.setText(f"Sessions: {len(getattr(item, 'session_ids', []))}  Cache: {len(getattr(cache, 'values', {}))}")
            self.line_type.setText(f"Diagnostics: {getattr(diagnostics, 'status', 'Ready')}")
            self.line_weight.setText("ParametricEngine subsystem; no MeshEntity updates")
        elif getattr(item, "is_sketch_solve_session", False):
            state = getattr(item, "state", None)
            diagnostics = getattr(item, "diagnostics", None)
            order = getattr(item, "evaluation_order", None)
            self.radius.setText(f"Sketch: {getattr(item, 'sketch_id', '') or 'Unassigned'}")
            self.width.setText(f"State: {getattr(state, 'state', 'Ready')}  Constraints: {len(getattr(order, 'constraint_ids', []))}")
            self.height.setText(f"Geometry: {len(getattr(order, 'geometry_ids', []))}  DOF: {getattr(state, 'dof_state', 'Under Constrained')}")
            self.line_type.setText(f"Diagnostics: {getattr(diagnostics, 'status', 'Ready')}")
            self.line_weight.setText("Renderer metadata only")
        elif getattr(item, "is_feature_execution_session", False):
            state = getattr(item, "state", None)
            diagnostics = getattr(item, "diagnostics", None)
            order = getattr(item, "evaluation_order", None)
            context = getattr(item, "context", None)
            self.radius.setText(f"Feature: {getattr(context, 'feature_id', '') or 'Timeline'}")
            self.width.setText(f"State: {getattr(state, 'status', 'Ready')}  Execution: {getattr(state, 'execution_status', 'Not Executed')}")
            self.height.setText(
                f"Ordered: {len(getattr(order, 'ordered_feature_ids', []))}  "
                f"Suppressed: {len(getattr(order, 'suppressed_feature_ids', []))}"
            )
            self.line_type.setText(f"Diagnostics: {getattr(diagnostics, 'status', 'Ready')}")
            self.line_weight.setText("Feature framework metadata only; no geometry generation")
        elif getattr(item, "is_geometry_kernel", False):
            state = getattr(item, "state", None)
            diagnostics = getattr(item, "diagnostics", None)
            self.radius.setText(f"Geometry Kernel: {getattr(item, 'name', 'Geometry Kernel')}")
            self.width.setText(f"Sessions: {len(getattr(item, 'session_ids', []))}  Topologies: {len(getattr(item, 'topology_ids', []))}")
            self.height.setText(f"State: {getattr(state, 'state', 'Ready')}  Mesh Sync: {getattr(state, 'mesh_sync_state', 'Pending')}")
            self.line_type.setText(f"Diagnostics: {getattr(diagnostics, 'status', 'Ready')}")
            self.line_weight.setText("ParametricEngine subsystem; BodyManager updates MeshEntity")
        elif getattr(item, "is_geometry_session", False):
            state = getattr(item, "state", None)
            result = getattr(item, "result", None)
            self.radius.setText(f"Feature: {getattr(item, 'feature_id', '') or 'Unassigned'}")
            self.width.setText(f"Body: {getattr(result, 'body_id', '') or 'Pending'}")
            self.height.setText(f"Topology: {getattr(result, 'topology_id', '') or 'Pending'}")
            self.line_type.setText(f"State: {getattr(state, 'state', 'Ready')}")
            self.line_weight.setText("FeatureManager → BodyManager → MeshEntity")
        elif getattr(item, "is_brep_topology", False):
            self.radius.setText(f"BRep Topology: {getattr(item, 'name', 'Topology')}")
            self.width.setText(f"Vertices: {len(getattr(item, 'vertex_ids', []))}  Edges: {len(getattr(item, 'edge_ids', []))}")
            self.height.setText(f"Faces: {len(getattr(item, 'face_ids', []))}  Solids: {len(getattr(item, 'solid_ids', []))}")
            self.line_type.setText(f"Validation: {getattr(item, 'validation_status', 'Pending')}")
            self.line_weight.setText("Topology metadata; MeshEntity remains renderable owner")
        elif getattr(item, "is_geometry_result", False):
            self.radius.setText(f"Geometry Result: {getattr(item, 'status', 'Ready')}")
            self.width.setText(f"Body: {getattr(item, 'body_id', '') or 'Unassigned'}")
            self.height.setText(f"Mesh: {getattr(item, 'mesh_entity_id', '') or 'Unassigned'}")
            self.line_type.setText(f"Faces: {getattr(item, 'face_count', 0)}  Edges: {getattr(item, 'edge_count', 0)}")
            self.line_weight.setText(getattr(item, "message", "Geometry metadata"))
        elif getattr(item, "is_execution_session", False):
            state = getattr(item, "state", None)
            self.radius.setText(f"Execution Session: {getattr(item, 'name', 'Execution Session')}")
            self.width.setText(f"Requests: {len(getattr(item, 'request_ids', []))}  Results: {len(getattr(item, 'result_ids', []))}")
            self.height.setText(f"Status: {getattr(state, 'status', 'Ready')}  Dirty: {getattr(state, 'dirty', False)}")
            self.line_type.setText(f"Execution Engine: {getattr(item, 'engine_id', '') or 'Unassigned'}")
            self.line_weight.setText("Session metadata for core execution")
        elif getattr(item, "is_execution_request", False):
            flags = getattr(item, "flags", None)
            metadata = getattr(item, "metadata", None)
            self.radius.setText(f"Execution Request: {getattr(item, 'name', 'Execution Request')}")
            self.width.setText(f"Target: {getattr(item, 'target_id', '') or 'Unassigned'}  Priority: {getattr(item, 'priority', 0)}")
            self.height.setText(f"Type: {getattr(item, 'request_type', 'Evaluate')}  Stage: {getattr(metadata, 'pipeline_stage', 'Execution Engine')}")
            self.line_type.setText(f"Queued: {getattr(flags, 'queued', False)}  Completed: {getattr(flags, 'completed', False)}")
            self.line_weight.setText("Expression/basic node execution only; no geometry")
        elif getattr(item, "is_execution_result", False):
            metadata = getattr(item, "metadata", None)
            self.radius.setText(f"Execution Result: {getattr(item, 'status', 'Completed')}")
            self.width.setText(f"Target: {getattr(item, 'target_id', '') or 'Unassigned'}")
            self.height.setText(f"Value: {getattr(item, 'value', None)}")
            self.line_type.setText(f"Stage: {getattr(metadata, 'pipeline_stage', 'Execution Engine')}")
            self.line_weight.setText(getattr(item, "message", "Execution metadata"))
        elif getattr(item, "is_execution_batch", False):
            self.radius.setText(f"Execution Batch: {getattr(item, 'name', 'Execution Batch')}")
            self.width.setText(f"Requests: {len(getattr(item, 'request_ids', []))}  Status: {getattr(item, 'status', 'Queued')}")
            self.height.setText(f"Priority: {getattr(item, 'priority', 0)}")
            self.line_type.setText("Batch scheduling metadata")
            self.line_weight.setText("No CAD, BIM, manufacturing, AI, or geometry execution")
        elif getattr(item, "is_execution_pipeline", False):
            self.radius.setText(f"Execution Pipeline: {getattr(item, 'name', 'Execution Pipeline')}")
            self.width.setText(f"Stages: {len(getattr(item, 'stages', []))}")
            self.height.setText(f"Geometry Generation: {getattr(item, 'geometry_generation_enabled', False)}")
            self.line_type.setText("Parameter → Expression → Dependency Graph → Execution Engine")
            self.line_weight.setText("FeatureManager and BodyManager remain placeholders in Batch A")
        elif getattr(item, "is_parametric_parameter", False):
            bindings = manager.parameter_manager.bindings_for(item) if manager is not None else []
            expressions = manager.parameter_manager.expressions_for(item) if manager is not None else []
            self.radius.setText(f"Type: {getattr(item, 'parameter_type', 'Float')}  Scope: {getattr(item, 'scope', 'Local')}")
            self.width.setText(f"Value: {getattr(item, 'value', '')}  Unit: {getattr(item, 'unit', '') or 'Unitless'}")
            self.height.setText(f"Expressions: {len(expressions)}  Bindings: {len(bindings)}")
            self.line_type.setText("Parameter metadata only")
            self.line_weight.setText("No evaluation or solving")
        elif getattr(item, "is_parameter_category", False):
            self.radius.setText(f"Category: {getattr(item, 'name', 'Parameter Category')}")
            self.width.setText(f"Type: {getattr(item, 'parameter_type', 'Float')}")
            self.height.setText(f"Parameters: {len(getattr(item, 'parameter_ids', []))}")
            self.line_type.setText("Parameter Category")
            self.line_weight.setText("Metadata only")
        elif getattr(item, "is_expression", False):
            context = getattr(item, "context", None)
            self.radius.setText(f"Expression: {getattr(item, 'text', '') or 'Empty'}")
            self.width.setText(f"Parameters: {len(getattr(context, 'referenced_parameter_ids', []))}")
            self.height.setText(f"Objects: {len(getattr(context, 'referenced_object_ids', []))}")
            self.line_type.setText(f"Validation: {getattr(item, 'validation_state', 'Not Parsed')}")
            self.line_weight.setText("No parsing or execution")
        elif getattr(item, "is_expression_binding", False):
            self.radius.setText(f"Binding: {getattr(item, 'binding_type', 'ParameterToExpression')}")
            self.width.setText(f"Source: {getattr(item, 'source_id', '') or 'Unassigned'}")
            self.height.setText(f"Target: {getattr(item, 'target_id', '') or 'Unassigned'}")
            self.line_type.setText(f"Expression: {getattr(item, 'expression_id', '') or 'None'}")
            self.line_weight.setText("Relationship storage only")
        elif getattr(item, "is_dependency_graph", False):
            flags = getattr(item, "flags", None)
            self.radius.setText(f"Graph: {getattr(item, 'name', 'Dependency Graph')}")
            self.width.setText(f"Nodes: {len(getattr(item, 'node_ids', []))}  Edges: {len(getattr(item, 'edge_ids', []))}")
            self.height.setText(f"Dirty: {getattr(flags, 'dirty', False)}  Pending: {getattr(flags, 'pending_evaluation', False)}")
            self.line_type.setText(f"Cycle: {getattr(flags, 'cycle_detection_status', 'Not Checked')}")
            self.line_weight.setText("Metadata only; no solving")
        elif getattr(item, "is_dependency_node", False):
            self.radius.setText(f"Node: {getattr(item, 'name', 'Dependency Node')}")
            self.width.setText(f"Type: {getattr(item, 'node_type', 'Object')}  Level: {getattr(item, 'dependency_level', 0)}")
            self.height.setText(f"In: {len(getattr(item, 'incoming_edge_ids', []))}  Out: {len(getattr(item, 'outgoing_edge_ids', []))}")
            self.line_type.setText(f"Dirty: {getattr(item, 'dirty', False)}  Pending: {getattr(item, 'pending_evaluation', False)}")
            self.line_weight.setText("Relationship topology metadata")
        elif getattr(item, "is_dependency_edge", False):
            self.radius.setText(f"Edge: {getattr(item, 'relationship', 'DependsOn')}")
            self.width.setText(f"Source Node: {getattr(item, 'source_id', '') or 'Unassigned'}")
            self.height.setText(f"Target Node: {getattr(item, 'target_id', '') or 'Unassigned'}")
            self.line_type.setText(f"Dirty: {getattr(item, 'dirty', False)}  Pending: {getattr(item, 'pending_evaluation', False)}")
            self.line_weight.setText("No propagation")
        elif getattr(item, "is_dependency_path", False):
            self.radius.setText(f"Path: {getattr(item, 'relationship', 'DependsOn')}")
            self.width.setText(f"Nodes: {len(getattr(item, 'node_ids', []))}")
            self.height.setText(f"Edges: {len(getattr(item, 'edge_ids', []))}")
            self.line_type.setText("Stored path metadata")
            self.line_weight.setText("No traversal")
        elif getattr(item, "is_dependency_topology", False):
            self.radius.setText("Dependency Topology")
            self.width.setText(f"Parents: {len(getattr(item, 'parent_map', {}))}  Children: {len(getattr(item, 'child_map', {}))}")
            self.height.setText(f"Dirty: {len(getattr(item, 'dirty_node_ids', []))}  Pending: {len(getattr(item, 'pending_evaluation_ids', []))}")
            self.line_type.setText(f"Cycle: {getattr(item, 'cycle_detection_status', 'Not Checked')}")
            self.line_weight.setText("Topology metadata only")
        elif getattr(item, "is_material_profile", False):
            self.radius.setText(f"Material: {getattr(item, 'material_type', 'Wood')}")
            self.width.setText(f"Thickness: {self._number(getattr(item, 'thickness', 0.0))}")
            self.line_type.setText("Laser/Plasma Material Profile")
            self.line_weight.setText(f"Supplier: {getattr(item, 'supplier_id', '') or 'None'}")
        elif getattr(item, "is_cutting_profile", False):
            self.radius.setText(f"Cut Speed: {self._number(getattr(item, 'cut_speed', 0.0))}")
            self.width.setText(f"Travel: {self._number(getattr(item, 'travel_speed', 0.0))}")
            self.height.setText(f"Passes: {getattr(item, 'pass_count', 1)}")
            self.line_type.setText(f"Material: {getattr(item, 'material_profile_id', '') or 'Unassigned'}")
            self.line_weight.setText(f"Kerf: {self._number(getattr(item, 'kerf_width', 0.0))}")
        elif getattr(item, "is_power_profile", False):
            self.radius.setText(f"Power: {self._number(getattr(item, 'laser_power', 0.0))}")
            self.width.setText(f"Min: {self._number(getattr(item, 'minimum_power', 0.0))}")
            self.height.setText(f"Max: {self._number(getattr(item, 'maximum_power', 0.0))}")
            self.line_type.setText("Laser Power Profile")
            self.line_weight.setText("Metadata Only")
        elif getattr(item, "is_tool_library", False):
            tools = manager.tools_for_library(item)
            holders = manager.holders_for_library(item)
            self.radius.setText(f"Tools: {len(tools)}  Holders: {len(holders)}")
            self.width.setText(f"Categories: {len(getattr(item, 'category_ids', []))}")
            self.line_type.setText("Tool Library")
            self.line_weight.setText("Future cloud library ready")
        elif getattr(item, "is_tool_category", False):
            tools = manager.tools_for_category(item)
            self.radius.setText(f"Tools: {len(tools)}")
            self.width.setText(f"Library: {getattr(item, 'library_id', '') or 'Unassigned'}")
            self.line_type.setText("Tool Category")
            self.line_weight.setText("Searchable")
        elif getattr(item, "is_tool_definition", False):
            metadata = getattr(item, "metadata", None)
            self.radius.setText(f"Diameter: {self._number(getattr(item, 'diameter', 0.0))}")
            self.width.setText(
                f"Flute: {self._number(getattr(item, 'flute_length', 0.0))}  "
                f"Overall: {self._number(getattr(item, 'overall_length', 0.0))}"
            )
            self.height.setText(f"Flutes: {getattr(item, 'flutes', 0)}")
            self.line_type.setText(f"Tool: {getattr(item, 'tool_type', 'Tool')}")
            self.line_weight.setText(
                f"Material: {getattr(metadata, 'material', '') or 'Unassigned'}  "
                f"Coating: {getattr(metadata, 'coating', '') or 'Unassigned'}"
            )
            self.angle.setText(
                f"Tip: {self._number(getattr(item, 'tip_angle', 0.0))}  "
                f"Corner: {self._number(getattr(item, 'corner_radius', 0.0))}"
            )
        elif getattr(item, "is_tool_holder", False):
            metadata = getattr(item, "metadata", None)
            self.radius.setText(f"Holder: {getattr(item, 'holder_type', 'Holder')}")
            self.width.setText(f"Length: {self._number(getattr(item, 'length', 0.0))}")
            self.height.setText(f"Gauge: {self._number(getattr(item, 'gauge_length', 0.0))}")
            self.line_type.setText(f"Standard: {getattr(metadata, 'holder_standard', '') or 'Placeholder'}")
            self.line_weight.setText(f"Library: {getattr(item, 'library_id', '') or 'Unassigned'}")
        elif getattr(item, "is_feed_speed_profile", False):
            cutting = getattr(item, "cutting_data", None)
            self.radius.setText(f"Spindle: {self._number(getattr(cutting, 'spindle_speed', 0.0))}")
            self.width.setText(f"Feed: {self._number(getattr(cutting, 'feed_rate', 0.0))}")
            self.height.setText(f"Plunge: {self._number(getattr(cutting, 'plunge_rate', 0.0))}")
            self.line_type.setText(f"Tool: {getattr(item, 'tool_id', '') or 'Unassigned'}")
            self.line_weight.setText(f"Material: {getattr(item, 'material_id', '') or 'Unassigned'}")
        elif getattr(item, "is_tool_preset", False):
            self.radius.setText(f"Tool Number: {getattr(item, 'tool_number', 0)}")
            self.width.setText(f"Tool: {getattr(item, 'tool_id', '') or 'Unassigned'}")
            self.height.setText(f"Holder: {getattr(item, 'holder_id', '') or 'Unassigned'}")
            self.line_type.setText(f"Length Offset: {getattr(item, 'length_offset', 0)}")
            self.line_weight.setText(f"Diameter Offset: {getattr(item, 'diameter_offset', 0)}")
        elif getattr(item, "is_body", False):
            features = [
                feature for feature in getattr(manager, "features", [])
                if feature.id in getattr(item, "feature_ids", [])
            ]
            self.radius.setText(f"Features: {len(features)}")
            self.line_type.setText(
                f"Mesh: {getattr(item, 'mesh_entity_id', '') or 'Unassigned'}"
            )
            self.line_weight.setText(
                "Visible" if getattr(item, "visible", True) else "Hidden"
            )
        elif getattr(item, "is_feature", False):
            definition = getattr(item, "definition", None)
            options = getattr(definition, "options", None)
            result = getattr(item, "result", None)
            execution_state = getattr(item, "execution_state", None)
            diagnostics = getattr(item, "diagnostics", None)
            state = manager.feature_editor.state_for(item)
            dependencies = manager.dependency_manager.dependencies_for(item)
            edge_selections = manager.edge_modification_manager.selections_for_feature(item)
            pattern_instances = (
                manager.pattern_manager.instances_for_feature(item)
                if getattr(item, "type_name", "") == "PatternFeature"
                else []
            )
            self.radius.setText(f"Type: {getattr(item, 'feature_type', 'Feature')}")
            self.length.setText(
                f"Distance: {self._number(getattr(options, 'distance', 0.0))}"
            )
            self.angle.setText(
                f"Angle: {self._number(getattr(options, 'angle', 0.0))}"
            )
            self.line_type.setText(
                f"Operation: {getattr(options, 'operation', 'Join')}"
            )
            self.line_weight.setText(
                "Dirty" if getattr(state, "dirty", False)
                else (
                    "Suppressed" if getattr(item, "suppressed", False)
                    else (
                        f"{getattr(execution_state, 'status', 'Ready')} / {getattr(execution_state, 'execution_status', 'Not Executed')}"
                        if execution_state is not None and getattr(execution_state, "execution_status", "Not Executed") != "Not Executed"
                        else "Active"
                    )
                )
            )
            self.height.setText(
                f"Result: {getattr(result, 'status', 'Pending')}  "
                f"Dependencies: {len(dependencies)}  "
                f"Diagnostics: {getattr(diagnostics, 'status', 'Ready')}"
            )
            if getattr(item, "type_name", "") in ("FilletFeature", "ChamferFeature"):
                self.width.setText(f"Edges: {len(edge_selections)}")
                if getattr(item, "type_name", "") == "FilletFeature":
                    self.radius.setText(f"Fillet Radius: {self._number(getattr(options, 'distance', 0.0))}")
                else:
                    self.radius.setText(f"Chamfer Distance: {self._number(getattr(options, 'distance', 0.0))}")
            elif getattr(item, "type_name", "") == "PatternFeature":
                pattern_definition = getattr(item, "pattern_definition", None)
                self.width.setText(f"Instances: {len(pattern_instances)}")
                self.radius.setText(
                    f"Pattern: {getattr(pattern_definition, 'pattern_type', 'Pattern')}"
                )
                self.diameter.setText(
                    f"Count: {getattr(pattern_definition, 'count', 0)}  "
                    f"Spacing: {self._number(getattr(pattern_definition, 'spacing', 0.0))}"
                )
            elif getattr(item, "is_surface_feature", False):
                surface_definition = getattr(item, "surface_definition", None)
                surface_options = getattr(surface_definition, "options", None)
                surface_result = getattr(item, "surface_result", None)
                self.radius.setText(f"Surface: {getattr(item, 'feature_type', 'Surface')}")
                self.width.setText(
                    f"Profiles: {len(getattr(surface_options, 'profile_ids', []))}  "
                    f"Curves: {len(getattr(surface_options, 'boundary_curve_ids', []))}"
                )
                self.diameter.setText(
                    f"Offset: {self._number(getattr(surface_options, 'offset_distance', 0.0))}  "
                    f"Continuity: {getattr(surface_options, 'continuity', 'G0')}"
                )
                self.height.setText(
                    f"Surface Result: {getattr(surface_result, 'status', 'Pending')}  "
                    f"Dependencies: {len(dependencies)}"
                )

    # -----------------------------------------

    def _show_annotation3d(self, annotation):

        self.type.setText(getattr(annotation, "type_name", "Annotation3D"))
        self.content.setText(annotation.text or annotation.annotation_type)
        self.alignment.setText(annotation.annotation_type)
        self.dimension_style.setText("Screen" if annotation.screen_space else "World")
        self.color.setText(annotation.display_color)
        self.visible.setChecked(getattr(annotation, "visible", True))
        self.locked.setChecked(getattr(annotation, "locked", False))
        self._populate_layers(getattr(annotation, "layer_name", ""))
        self._show_layer_properties(annotation)

        if annotation.points:
            first = annotation.points[0]
            self.x.setText(self._number(first.x))
            self.y.setText(self._number(first.y))
            self.x2.setText(self._number(first.z))

        review_manager = getattr(self.workspace, "review_manager", None)

        if review_manager is not None:
            linked = review_manager.linked_to(annotation)

            if linked:
                item = linked[0]
                self.line_type.setText(f"Review: {item.status}")
                self.line_weight.setText(f"Priority: {item.priority}")

    # -----------------------------------------

    def _show_issue(self, issue):

        self.type.setText(getattr(issue, "type_name", "Issue"))
        self.content.setText(issue.title)
        self.alignment.setText(issue.status)
        self.dimension_style.setText(issue.category)
        self.line_type.setText(f"Assignee: {issue.assignee or 'Unassigned'}")
        self.line_weight.setText(f"Priority: {issue.priority}")
        self.color.setText(issue.display_color)
        self.visible.setChecked(getattr(issue, "visible", True))
        self.locked.setChecked(getattr(issue, "locked", False))
        self._populate_layers(getattr(issue, "layer_name", ""))
        self._show_layer_properties(issue)
        self.x.setText(self._number(issue.position.x))
        self.y.setText(self._number(issue.position.y))
        self.x2.setText(self._number(issue.position.z))

        collaboration = getattr(self.workspace, "collaboration_manager", None)

        if collaboration is not None and collaboration.active is not None:
            self.radius.setText(f"Session: {collaboration.active.name}")

    # -----------------------------------------

    def _show_reference(self, reference):

        manager = getattr(self.workspace, "reference_manager", None)
        model = (
            manager.get_model(reference.model_id)
            if manager is not None else None
        )

        self.type.setText(getattr(reference, "type_name", "ReferenceInstance"))
        self.content.setText(reference.name)
        self.alignment.setText(f"Model: {getattr(model, 'name', reference.model_id)}")
        self.dimension_style.setText(getattr(model, "path", ""))
        self.line_type.setText(f"Status: {getattr(model, 'status', 'Unknown')}")
        self.line_weight.setText(f"Group: {getattr(model, 'group', '')}")
        self.color.setText(getattr(reference, "display_color", "#90caf9"))
        self.visible.setChecked(getattr(reference, "visible", True))
        self.locked.setChecked(getattr(reference, "locked", False))
        self._populate_layers(getattr(reference, "layer_name", ""))
        self._show_layer_properties(reference)

        position = reference.transform.position
        scale = reference.transform.scale
        rotation = reference.transform.rotation
        self.x.setText(self._number(position.x))
        self.y.setText(self._number(position.y))
        self.x2.setText(self._number(position.z))
        self.width.setText(self._number(scale.x))
        self.height.setText(self._number(scale.y))
        self.radius.setText(self._number(scale.z))
        self.length.setText(self._number(rotation.x))
        self.angle.setText(self._number(rotation.y))
        self.diameter.setText(self._number(rotation.z))

        if model is not None and getattr(model, "reader_type", ""):
            stats = getattr(model, "import_statistics", None)
            self.alignment.setText(f"Reader: {model.reader_type}")

            if stats is not None:
                self.line_type.setText(
                    f"Mesh: {stats.vertices} V / {stats.faces} F"
                )
                self.line_weight.setText(
                    f"Warnings: {stats.warnings}  Errors: {stats.errors}"
                )

            layer_stats = manager.layer_statistics(model) if manager is not None else None

            if layer_stats is not None:
                self.dimension_style.setText(
                    f"Ref Layers: {layer_stats['visible']}/{layer_stats['layers']} visible"
                )

            style = getattr(model, "style_overrides", None)

            if style is not None:
                self.color.setText(
                    f"{style.display_color}  T:{style.transparency:.2f}  Mode:{style.display_mode_override}"
                )

            coordination = getattr(model, "coordination_ui_settings", {})
            self.diameter.setText(coordination.get("validation_status", "Unchecked"))

    # -----------------------------------------

    def _show_clash(self, clash):

        self.type.setText(getattr(clash, "type_name", "ClashResult"))
        self.visible.setChecked(getattr(clash, "visible", True))
        self.locked.setChecked(getattr(clash, "locked", False))
        self._populate_layers(getattr(clash, "layer_name", ""))
        self._show_layer_properties(clash)
        self.content.setText(clash.description)
        self.alignment.setText(clash.clash_type)
        self.dimension_style.setText(
            f"{clash.status} | Reviewer: {clash.assigned_reviewer or 'Unassigned'} | "
            f"Owner: {clash.owner or 'Unassigned'}"
        )
        self.line_type.setText(f"{clash.entity_a_name} vs {clash.entity_b_name}")
        self.line_weight.setText(
            f"Severity: {clash.severity} | Priority: {clash.priority} | Approval: {clash.approval_state}"
        )
        self.color.setText(clash.display_color)
        if clash.comments:
            self.length.setText(clash.comments)
        if clash.resolution_notes:
            self.angle.setText(clash.resolution_notes)
        if clash.due_date or clash.discipline:
            self.diameter.setText(f"Due: {clash.due_date or 'None'} | Discipline: {clash.discipline or 'Unassigned'}")
        if clash.linked_issue_id or clash.linked_review_id:
            self.alignment.setText(
                f"{clash.clash_type} | Issue: {clash.linked_issue_id or 'None'} | "
                f"Review: {clash.linked_review_id or 'None'}"
            )
        self.x.setText(self._number(clash.location.x))
        self.y.setText(self._number(clash.location.y))
        self.x2.setText(self._number(clash.location.z))

        box = clash.bounding_box3d

        if box.valid:
            size = box.size
            self.width.setText(self._number(size.x))
            self.height.setText(self._number(size.y))
            self.radius.setText(self._number(size.z))

    # -----------------------------------------

    def _show_compare_result(self, result):

        self.type.setText(getattr(result, "type_name", "CompareResult"))
        self.visible.setChecked(getattr(result, "visible", True))
        self.locked.setChecked(getattr(result, "locked", False))
        self.content.setText(result.description)
        self.alignment.setText(result.change_type)
        self.dimension_style.setText(f"Object: {result.object_id}")
        before = result.before.get("name", "None") if result.before else "None"
        after = result.after.get("name", "None") if result.after else "None"
        self.line_type.setText(f"{before} → {after}")
        self.line_weight.setText(
            f"Source: {result.after.get('source', result.before.get('source', 'Unknown'))}"
        )
        self.color.setText(result.display_color)
        self.x.setText(self._number(result.location.x))
        self.y.setText(self._number(result.location.y))
        self.x2.setText(self._number(result.location.z))

        box = result.bounding_box3d

        if box.valid:
            size = box.size
            self.width.setText(self._number(size.x))
            self.height.setText(self._number(size.y))
            self.radius.setText(self._number(size.z))

    # -----------------------------------------

    def _show_revision(self, revision):

        self.type.setText(getattr(revision, "type_name", "Revision"))
        self.visible.setChecked(getattr(revision, "visible", True))
        self.locked.setChecked(getattr(revision, "locked", False))
        self.content.setText(revision.metadata.description or revision.name)
        self.alignment.setText(f"Source: {revision.metadata.source}")
        self.dimension_style.setText(f"Author: {revision.metadata.author or 'Unknown'}")
        self.line_type.setText(f"Objects: {revision.statistics.object_count}")
        self.line_weight.setText(
            f"Changes: {revision.statistics.change_count} | References: {revision.statistics.reference_count}"
        )
        self.color.setText(revision.display_color)
        self.length.setText(f"Added: {revision.statistics.added}")
        self.angle.setText(f"Removed: {revision.statistics.removed}")
        self.diameter.setText(f"Modified: {revision.statistics.modified}")
        self.x.setText(self._number(revision.location.x))
        self.y.setText(self._number(revision.location.y))
        self.x2.setText(self._number(revision.location.z))

        if revision.metadata.tags:
            self.radius.setText(", ".join(revision.metadata.tags))

    # -----------------------------------------

    def _show_coordination_package(self, package):

        self.type.setText(getattr(package, "type_name", "CoordinationPackage"))
        self.visible.setChecked(getattr(package, "visible", True))
        self.locked.setChecked(getattr(package, "locked", False))
        self.content.setText(package.metadata.description or package.name)
        self.alignment.setText(f"Status: {package.metadata.status}")
        self.dimension_style.setText(f"Version: {package.metadata.version}")
        self.line_type.setText(
            f"Refs: {package.statistics.references} | BCF: {package.statistics.bcf_topics}"
        )
        self.line_weight.setText(
            f"Clashes: {package.statistics.clashes} | Revisions: {package.statistics.revisions}"
        )
        self.color.setText(package.display_color)
        self.length.setText(f"Issues: {package.statistics.issues}")
        self.angle.setText(f"Reviews: {package.statistics.reviews}")
        self.diameter.setText(f"Validation: {package.validation.status}")
        self.x.setText(self._number(package.location.x))
        self.y.setText(self._number(package.location.y))
        self.x2.setText(self._number(package.location.z))

        if package.validation.errors:
            self.radius.setText("; ".join(package.validation.errors))
        elif package.validation.warnings:
            self.radius.setText("; ".join(package.validation.warnings))

    # -----------------------------------------

    def _show_bcf_topic(self, topic):

        self.type.setText(getattr(topic, "type_name", "BCFTopic"))
        self.visible.setChecked(getattr(topic, "visible", True))
        self.locked.setChecked(getattr(topic, "locked", False))
        self.content.setText(getattr(topic, "title", ""))
        self.alignment.setText(getattr(topic, "topic_type", "Coordination"))
        self.dimension_style.setText(
            f"{getattr(topic, 'status', 'Open')} | Priority: {getattr(topic, 'priority', 'Normal')}"
        )
        self.line_type.setText(
            f"Clash: {getattr(topic, 'linked_clash_id', '') or 'None'} | "
            f"Issue: {getattr(topic, 'linked_issue_id', '') or 'None'}"
        )
        self.line_weight.setText(
            f"Review: {getattr(topic, 'linked_review_id', '') or 'None'} | "
            f"Reference: {getattr(topic, 'linked_reference_id', '') or 'None'}"
        )
        self.color.setText(getattr(topic, "display_color", ""))
        self.length.setText(f"Comments: {len(getattr(topic, 'comments', []))}")
        self.angle.setText(f"Viewpoints: {len(getattr(topic, 'viewpoints', []))}")
        self.diameter.setText(f"Snapshots: {len(getattr(topic, 'snapshots', []))}")

        location = getattr(topic, "location", None)

        if location is not None:
            self.x.setText(self._number(location.x))
            self.y.setText(self._number(location.y))
            self.x2.setText(self._number(location.z))

    # -----------------------------------------

    def _show_section(self, section):

        self.type.setText(getattr(section, "type_name", "SectionPlane"))
        self.content.setText(section.name)
        self.alignment.setText("Enabled" if section.enabled else "Disabled")
        self.dimension_style.setText("Active" if self._active_section() is section else "Section")
        self.color.setText(section.display_color)
        self.length.setText(self._number(section.size))
        self.x.setText(self._number(section.origin.x))
        self.y.setText(self._number(section.origin.y))
        self.x2.setText(self._number(section.origin.z))
        self.width.setText(self._number(section.normal.x))
        self.height.setText(self._number(section.normal.y))
        self.radius.setText(self._number(section.normal.z))

        manager = getattr(self.workspace, "section_manager", None)
        view_manager = getattr(self.workspace, "view_state_manager", None)
        display_manager = getattr(self.workspace, "display_mode_manager", None)
        style_manager = getattr(self.workspace, "visual_style_manager", None)
        collection_manager = getattr(self.workspace, "scene_collection_manager", None)
        filter_manager = getattr(self.workspace, "view_filter_manager", None)
        preset_manager = getattr(self.workspace, "display_preset_manager", None)

        if manager is not None:
            clipping = "Clip ON" if manager.clipping.clip_toggle else "Clip OFF"
            self.line_type.setText(clipping)
            self.line_weight.setText(
                f"Plane {manager.clipping.plane_enabled} Box {manager.clipping.box_enabled}"
            )

        if view_manager is not None:
            current_view = getattr(view_manager, "current", None)
            self.dimension_style.setText(f"View: {getattr(current_view, 'name', 'Unsaved')}")

        if display_manager is not None:
            self.line_weight.setText(f"Display: {display_manager.current_mode}")

        if style_manager is not None:
            current_style = getattr(style_manager, "current", None)
            self.color.setText(f"Style: {getattr(current_style, 'name', 'Default')}")

        if collection_manager is not None:
            collection = collection_manager.entity_collection(section)
            if collection is not None:
                self.content.setText(f"{section.name} | Collection: {collection.name}")

        if filter_manager is not None:
            active_filter = getattr(filter_manager, "active", None)
            if active_filter is not None:
                self.alignment.setText(f"Filter: {active_filter.name}")

        if preset_manager is not None:
            active_preset = getattr(preset_manager, "active", None)
            if active_preset is not None:
                self.dimension_style.setText(f"Preset: {active_preset.name}")

    # -----------------------------------------

    def _active_section(self):

        manager = getattr(self.workspace, "section_manager", None)

        if manager is None:
            return None

        return manager.active

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

    def _show_text(self, entity):

        self.x.setText(self._number(entity.position.x))
        self.y.setText(self._number(entity.position.y))
        self.height.setText(self._number(entity.height))
        self.angle.setText(self._number(getattr(entity, "rotation", 0.0)))
        self.content.setText(str(entity.text or "").replace("\n", "\\n"))
        self.alignment.setText(getattr(entity, "alignment", "Left"))

    # -----------------------------------------

    def _show_mtext(self, entity):

        self.x.setText(self._number(entity.position.x))
        self.y.setText(self._number(entity.position.y))
        self.width.setText(self._number(entity.box_width))
        self.height.setText(self._number(entity.box_height))
        self.length.setText(self._number(entity.height))
        self.angle.setText(self._number(getattr(entity, "rotation", 0.0)))
        self.content.setText(str(entity.text or "").replace("\n", "\\n"))
        self.alignment.setText(getattr(entity, "alignment", "Left"))

    # -----------------------------------------

    def _show_leader(self, entity):

        self.x.setText(self._number(entity.arrow_point.x))
        self.y.setText(self._number(entity.arrow_point.y))
        self.x2.setText(self._number(entity.landing_end.x))
        self.y2.setText(self._number(entity.landing_end.y))
        self.height.setText(self._number(entity.text_entity.height))
        self.content.setText(str(entity.text_entity.text or "").replace("\n", "\\n"))

    # -----------------------------------------

    def _show_dimension(self, entity):

        points = entity.definition_points()

        if points:
            self.x.setText(self._number(points[0].x))
            self.y.setText(self._number(points[0].y))

        if len(points) > 1:
            self.x2.setText(self._number(points[1].x))
            self.y2.setText(self._number(points[1].y))

        if len(points) > 2:
            self.width.setText(self._number(points[2].x))
            self.height.setText(self._number(points[2].y))

        self.radius.setText(self._number(entity.measurement()))
        self.content.setText(getattr(entity, "text_override", ""))
        self.dimension_style.setText(getattr(entity, "dimension_style_name", ""))

    # -----------------------------------------

    def _show_hatch(self, entity):

        box = entity.bounding_box
        self.x.setText(self._number(box.min.x))
        self.y.setText(self._number(box.min.y))
        self.width.setText(self._number(box.width))
        self.height.setText(self._number(box.height))
        self.content.setText(getattr(entity, "pattern_name", "SOLID"))
        self.angle.setText(self._number(getattr(entity, "pattern_angle", 0.0)))
        self.length.setText(self._number(getattr(entity, "pattern_scale", 1.0)))
        self.alignment.setText("Associative" if getattr(entity, "associative", False) else "Static")

    # -----------------------------------------

    def _show_curve(self, entity):

        points = self._curve_points(entity)

        if points:
            self.x.setText(self._number(points[0].x))
            self.y.setText(self._number(points[0].y))

        if len(points) > 1:
            self.x2.setText(self._number(points[-1].x))
            self.y2.setText(self._number(points[-1].y))

        box = entity.bounding_box
        self.width.setText(self._number(box.width if points else 0.0))
        self.height.setText(self._number(box.height if points else 0.0))
        self.length.setText(self._number(getattr(entity, "length", 0.0)))
        self.radius.setText(str(len(points)))
        self.content.setText(self._curve_points_text(points))
        self.alignment.setText("Closed" if getattr(entity, "closed", False) else "Open")

    # -----------------------------------------

    def _show_constraint(self, constraint):

        self.layer.setEnabled(False)
        self.visible.setChecked(constraint.enabled)
        self.locked.setChecked(constraint.suppressed)
        self.content.setText(constraint.name)
        self.alignment.setText(constraint.status)
        self.dimension_style.setText(constraint.constraint_type)
        self.radius.setText("" if constraint.value is None else self._number(constraint.value))
        self.length.setText(str(constraint.referenced_entity_count()))
        self.angle.setText("Driven" if constraint.driven else "Driving")
        self.color.setText(constraint.category)
        self.line_type.setText(constraint.message)

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

        if getattr(self.selected[0], "is_constraint", False):
            self._execute_constraint_update(
                self.selected[0],
                {
                    "enabled": bool(state),
                    "suppressed": not bool(state),
                },
            )
            return

        self._execute_entity_update(self.selected[0], {"visible": bool(state)})

    # -----------------------------------------

    def _locked_changed(self, state):

        if self._ignore_edit():
            return

        if getattr(self.selected[0], "is_constraint", False):
            self._execute_constraint_update(
                self.selected[0],
                {
                    "suppressed": bool(state),
                    "enabled": not bool(state),
                },
            )
            return

        self._execute_entity_update(self.selected[0], {"locked": bool(state)})

    # -----------------------------------------

    def _geometry_changed(self, field):

        if self._ignore_edit():
            return

        entity = self.selected[0]
        state = self._edited_geometry_state(entity, field)

        if state:
            command = state.pop("__command__", None)

            if command is not None:
                self.workspace.command_manager.execute(command)
                self._changed()
                return

            if getattr(entity, "is_constraint", False):
                self._execute_constraint_update(entity, state)
                return

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

        if getattr(entity, "is_3d", False):
            return self._3d_state(entity, field)

        if getattr(entity, "is_constraint", False):
            return self._constraint_state(entity, field)

        if getattr(entity, "is_hatch", False):
            return self._hatch_state(entity, field)

        if getattr(entity, "is_curve", False):
            return self._curve_state(entity, field)

        if hasattr(entity, "start") and hasattr(entity, "end"):
            return self._line_state(entity, field)

        if getattr(entity, "is_dimension", False):
            return self._dimension_state(entity, field)

        if hasattr(entity, "p1") and hasattr(entity, "p2"):
            return self._rectangle_state(entity, field)

        if hasattr(entity, "center") and hasattr(entity, "radius"):
            return self._circle_state(entity, field)

        if hasattr(entity, "text_entity"):
            return self._leader_state(entity, field)

        if hasattr(entity, "box_width") and hasattr(entity, "box_height"):
            return self._mtext_state(entity, field)

        if hasattr(entity, "position") and hasattr(entity, "text"):
            return self._text_state(entity, field)

        return {}

    # -----------------------------------------

    def _constraint_state(self, constraint, field):

        if field == "content":
            return {"name": self.content.text().strip() or constraint.name}

        if field == "radius":
            value = self._float(self.radius)

            if value is None:
                self.show_selection(self.selected)
                return {}

            return {"value": value}

        if field == "angle":
            mode = self.angle.text().strip().lower()

            return {"driven": mode == "driven"}

        return {}

    # -----------------------------------------

    def _3d_state(self, entity, field):

        position = getattr(entity, "position3d", Vector3()).copy()
        rotation = getattr(entity, "rotation3d", Vector3()).copy()
        scale = getattr(entity, "scale3d", Vector3(1.0, 1.0, 1.0)).copy()

        if field in ("x", "y", "content"):
            target = position.copy()

            if field == "x":
                target.x = self._float(self.x, target.x)
            elif field == "y":
                target.y = self._float(self.y, target.y)
            else:
                target.z = self._float(self.content, target.z)

            return {
                "__command__": TranslateEntity3DCommand(
                    self.workspace,
                    [entity],
                    target - position,
                )
            }

        if field in ("length", "angle", "radius"):
            delta = Vector3()

            if field == "length":
                delta.x = self._float(self.length, rotation.x) - rotation.x
            elif field == "angle":
                delta.y = self._float(self.angle, rotation.y) - rotation.y
            else:
                delta.z = self._float(self.radius, rotation.z) - rotation.z

            return {
                "__command__": RotateEntity3DCommand(
                    self.workspace,
                    [entity],
                    delta,
                    pivot=self.workspace.transform_gizmo.pivot_for_selection([entity]),
                )
            }

        if field in ("width", "height", "diameter"):
            target = scale.copy()

            if field == "width":
                target.x = max(0.0001, self._float(self.width, target.x))
            elif field == "height":
                target.y = max(0.0001, self._float(self.height, target.y))
            else:
                target.z = max(0.0001, self._float(self.diameter, target.z))

            factor = Vector3(
                target.x / (scale.x or 1.0),
                target.y / (scale.y or 1.0),
                target.z / (scale.z or 1.0),
            )

            return {
                "__command__": ScaleEntity3DCommand(
                    self.workspace,
                    [entity],
                    factor,
                    pivot=self.workspace.transform_gizmo.pivot_for_selection([entity]),
                )
            }

        if field == "alignment" and self.workspace is not None:
            gizmo = getattr(self.workspace, "transform_gizmo", None)
            coordinate_manager = getattr(self.workspace, "coordinate_system_manager", None)
            plane_manager = getattr(self.workspace, "construction_plane_manager", None)

            if gizmo is not None:
                tokens = self.alignment.text().strip().lower().split()

                for token in tokens:
                    if token in ("world", "local"):
                        gizmo.set_coordinate_mode(token)
                    elif token in ("center", "origin", "individual", "bounding_box_center"):
                        gizmo.set_pivot_mode(token)

            if coordinate_manager is not None:
                for token in self.alignment.text().strip().split():
                    if token in coordinate_manager.names():
                        coordinate_manager.activate(token)

            if plane_manager is not None:
                for token in self.alignment.text().strip().split():
                    if token in plane_manager.names():
                        plane_manager.set_active(token)

            return {}

        if hasattr(entity, "position") and field in ("x", "y"):
            position = entity.position.copy()

            if field == "x":
                position.x = self._float(self.x, position.x)
            else:
                position.y = self._float(self.y, position.y)

            return {"position": position}

        if hasattr(entity, "start") and hasattr(entity, "end"):
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
            else:
                return {}

            return {"start": start, "end": end}

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

    def _text_state(self, entity, field):

        position = entity.position.copy()
        height = entity.height
        rotation = getattr(entity, "rotation", 0.0)
        text = entity.text
        alignment = getattr(entity, "alignment", "Left")

        if field == "x":
            position.x = self._float(self.x, position.x)
        elif field == "y":
            position.y = self._float(self.y, position.y)
        elif field == "height":
            height = max(1.0, self._float(self.height, height))
        elif field == "angle":
            rotation = self._float(self.angle, rotation)
        elif field == "content":
            text = self.content.text().replace("\\n", "\n")
        elif field == "alignment":
            alignment = self.alignment.text().strip() or alignment
        else:
            return {}

        return {
            "position": position,
            "height": height,
            "rotation": rotation,
            "text": text,
            "alignment": alignment,
        }

    # -----------------------------------------

    def _mtext_state(self, entity, field):

        position = entity.position.copy()
        box_width = entity.box_width
        box_height = entity.box_height
        text_height = entity.height
        rotation = getattr(entity, "rotation", 0.0)
        text = entity.text
        alignment = getattr(entity, "alignment", "Left")

        if field == "x":
            position.x = self._float(self.x, position.x)
        elif field == "y":
            position.y = self._float(self.y, position.y)
        elif field == "width":
            box_width = max(1.0, self._float(self.width, box_width))
        elif field == "height":
            box_height = max(1.0, self._float(self.height, box_height))
        elif field == "length":
            text_height = max(1.0, self._float(self.length, text_height))
        elif field == "angle":
            rotation = self._float(self.angle, rotation)
        elif field == "content":
            text = self.content.text().replace("\\n", "\n")
        elif field == "alignment":
            alignment = self.alignment.text().strip() or alignment
        else:
            return {}

        return {
            "position": position,
            "box_width": box_width,
            "box_height": box_height,
            "height": text_height,
            "rotation": rotation,
            "text": text,
            "alignment": alignment,
        }

    # -----------------------------------------

    def _leader_state(self, entity, field):

        arrow_point = entity.arrow_point.copy()
        landing_start = entity.landing_start.copy()
        landing_end = entity.landing_end.copy()
        text_entity = entity.text_entity.clone()

        if field == "x":
            arrow_point.x = self._float(self.x, arrow_point.x)
        elif field == "y":
            arrow_point.y = self._float(self.y, arrow_point.y)
        elif field in ("x2", "y2"):
            old_end = landing_end.copy()

            if field == "x2":
                landing_end.x = self._float(self.x2, landing_end.x)
            else:
                landing_end.y = self._float(self.y2, landing_end.y)

            dx = landing_end.x - old_end.x
            dy = landing_end.y - old_end.y
            landing_start.x += dx
            landing_start.y += dy
            text_entity.move(dx, dy)
        elif field == "height":
            text_entity.height = max(1.0, self._float(self.height, text_entity.height))
        elif field == "content":
            text_entity.text = self.content.text().replace("\\n", "\n")
        else:
            return {}

        return {
            "arrow_point": arrow_point,
            "landing_start": landing_start,
            "landing_end": landing_end,
            "text_entity": text_entity,
        }

    # -----------------------------------------

    def _dimension_state(self, entity, field):

        fields = self._dimension_point_fields(entity)
        state = {key: value.copy() for key, value in fields.items()}
        state["text_override"] = getattr(entity, "text_override", "")
        state["dimension_style"] = getattr(entity, "dimension_style", None)
        state["dimension_style_id"] = getattr(entity, "dimension_style_id", None)
        state["dimension_style_name"] = getattr(entity, "dimension_style_name", None)

        if field == "x" and fields:
            first = next(iter(fields))
            state[first].x = self._float(self.x, state[first].x)
        elif field == "y" and fields:
            first = next(iter(fields))
            state[first].y = self._float(self.y, state[first].y)
        elif field == "x2" and len(fields) > 1:
            key = list(fields.keys())[1]
            state[key].x = self._float(self.x2, state[key].x)
        elif field == "y2" and len(fields) > 1:
            key = list(fields.keys())[1]
            state[key].y = self._float(self.y2, state[key].y)
        elif field == "width" and len(fields) > 2:
            key = list(fields.keys())[2]
            state[key].x = self._float(self.width, state[key].x)
        elif field == "height" and len(fields) > 2:
            key = list(fields.keys())[2]
            state[key].y = self._float(self.height, state[key].y)
        elif field == "content":
            state["text_override"] = self.content.text()
        elif field == "dimension_style":
            style = self._dimension_style_from_field()

            if style is None:
                self.show_selection(self.selected)
                return {}

            state["dimension_style"] = style
            state["dimension_style_id"] = style.id
            state["dimension_style_name"] = style.name
        else:
            return {}

        return state

    # -----------------------------------------

    def _hatch_state(self, entity, field):

        state = {
            "pattern": getattr(entity, "pattern", None),
            "pattern_name": getattr(entity, "pattern_name", "SOLID"),
            "pattern_scale": getattr(entity, "pattern_scale", 1.0),
            "pattern_angle": getattr(entity, "pattern_angle", 0.0),
        }

        if field == "content":
            pattern = self._pattern_from_field()

            if pattern is None:
                self.show_selection(self.selected)
                return {}

            state["pattern"] = pattern
            state["pattern_name"] = pattern.name
        elif field == "length":
            value = self._float(self.length)

            if value is None:
                self.show_selection(self.selected)
                return {}

            state["pattern_scale"] = max(1.0, value)
        elif field == "angle":
            state["pattern_angle"] = self._float(self.angle, state["pattern_angle"])
        else:
            return {}

        return state

    # -----------------------------------------

    def _curve_state(self, entity, field):

        attribute = "control_points" if hasattr(entity, "control_points") else "points"
        points = clone_points(getattr(entity, attribute, []))
        state = {attribute: points}

        if field in ("x", "y") and points:
            if field == "x":
                points[0].x = self._float(self.x, points[0].x)
            else:
                points[0].y = self._float(self.y, points[0].y)
        elif field in ("x2", "y2") and points:
            if field == "x2":
                points[-1].x = self._float(self.x2, points[-1].x)
            else:
                points[-1].y = self._float(self.y2, points[-1].y)
        elif field == "content":
            parsed = self._parse_curve_points(self.content.text())

            if len(parsed) < 2:
                self.show_selection(self.selected)
                return {}

            state[attribute] = parsed
        elif field == "alignment" and hasattr(entity, "closed"):
            state["closed"] = self.alignment.text().strip().lower() in (
                "closed",
                "true",
                "yes",
                "1",
            )
        else:
            return {}

        return state

    # -----------------------------------------

    def _pattern_from_field(self):

        name = self.content.text().strip()

        if not name or self.workspace is None:
            return None

        return self.workspace.pattern_manager.get(name)

    # -----------------------------------------

    def _curve_points(self, entity):

        if hasattr(entity, "control_points"):
            return entity.control_points

        return getattr(entity, "points", [])

    # -----------------------------------------

    def _curve_points_text(self, points):

        return "; ".join(
            f"{self._number(point.x)},{self._number(point.y)}"
            for point in points
        )

    # -----------------------------------------

    def _parse_curve_points(self, text):

        points = []

        for chunk in str(text or "").replace("|", ";").split(";"):
            chunk = chunk.strip()

            if not chunk:
                continue

            parts = [part.strip() for part in chunk.split(",")]

            if len(parts) != 2:
                return []

            try:
                points.append(Vector2(float(parts[0]), float(parts[1])))
            except ValueError:
                return []

        return points

    # -----------------------------------------

    def _dimension_point_fields(self, entity):

        if hasattr(entity, "vertex") and hasattr(entity, "point1") and hasattr(entity, "point2"):
            return {
                "vertex": entity.vertex,
                "point1": entity.point1,
                "point2": entity.point2,
                "arc_point": entity.arc_point,
            }

        if hasattr(entity, "point1") and hasattr(entity, "point2"):
            fields = {
                "point1": entity.point1,
                "point2": entity.point2,
            }

            if hasattr(entity, "dimension_point"):
                fields["dimension_point"] = entity.dimension_point
            elif hasattr(entity, "arc_point"):
                fields["arc_point"] = entity.arc_point

            return fields

        if hasattr(entity, "center") and hasattr(entity, "radius_point"):
            return {
                "center": entity.center,
                "radius_point": entity.radius_point,
                "text_point": entity.text_point,
            }

        return {}

    # -----------------------------------------

    def _dimension_style_from_field(self):

        name = self.dimension_style.text().strip()

        if not name or self.workspace is None:
            return None

        return self.workspace.dimension_style_manager.get(name)

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

    def _execute_constraint_update(self, constraint, after_values):

        before = self._entity_state(constraint, after_values)
        after = dict(before)
        after.update(after_values)

        if after == before:
            self.show_selection(self.selected)
            return

        command = UpdateConstraintCommand(self.workspace, constraint, before, after)
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
            self.content,
            self.alignment,
            self.dimension_style,
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
            text = field.text()

            if ":" in text:
                text = text.split(":", 1)[1].strip()

            return float(text)
        except ValueError:
            if fallback is not None:
                return fallback

            return None

    # -----------------------------------------

    def _number(self, value):

        return f"{value:.2f}"

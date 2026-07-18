from datetime import datetime, timezone
from uuid import uuid4

from engine.geometry import BoundingBox3D, MeshData, Vector3
from engine.import3d import ImportSettings, ImportStatistics


REFERENCE_STATUSES = ("Loaded", "Unloaded", "Missing", "Stale", "Error")


class ReferenceLayerMapping:
    """Display and edit state for a layer inside an external reference."""

    def __init__(
        self,
        name="Default",
        target_layer="0",
        visible=True,
        locked=False,
        isolated=False,
        color_override="",
    ):

        self.name = str(name or "Default")
        self.target_layer = str(target_layer or "0")
        self.visible = bool(visible)
        self.locked = bool(locked)
        self.isolated = bool(isolated)
        self.color_override = str(color_override or "")

    def to_dict(self):
        """Return JSON-safe layer mapping data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create layer mapping from persisted data."""

        data = data or {}

        return ReferenceLayerMapping(
            data.get("name", "Default"),
            data.get("target_layer", "0"),
            data.get("visible", True),
            data.get("locked", False),
            data.get("isolated", False),
            data.get("color_override", ""),
        )


class ReferenceStyleOverrides:
    """Display style override state for an external reference."""

    def __init__(
        self,
        display_color="#90caf9",
        transparency=0.0,
        wireframe_override=False,
        hidden_line_override=False,
        shaded_override=False,
        xray_override=False,
        display_mode_override="Default",
        selection_highlight_override="#ffeb3b",
        preset_name="Default",
    ):

        self.display_color = display_color
        self.transparency = float(transparency)
        self.wireframe_override = bool(wireframe_override)
        self.hidden_line_override = bool(hidden_line_override)
        self.shaded_override = bool(shaded_override)
        self.xray_override = bool(xray_override)
        self.display_mode_override = display_mode_override
        self.selection_highlight_override = selection_highlight_override
        self.preset_name = preset_name

    def to_dict(self):
        """Return JSON-safe style override data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create style override state from persisted data."""

        data = data or {}

        return ReferenceStyleOverrides(
            data.get("display_color", "#90caf9"),
            data.get("transparency", 0.0),
            data.get("wireframe_override", False),
            data.get("hidden_line_override", False),
            data.get("shaded_override", False),
            data.get("xray_override", False),
            data.get("display_mode_override", "Default"),
            data.get("selection_highlight_override", "#ffeb3b"),
            data.get("preset_name", "Default"),
        )


class ReferenceMetadata:
    """External reference metadata."""

    def __init__(self, author="", source_format="", created_at=None, modified_at=None):

        self.author = author
        self.source_format = source_format
        self.created_at = created_at or _timestamp()
        self.modified_at = modified_at or self.created_at

    def touch(self):
        """Refresh modification timestamp."""

        self.modified_at = _timestamp()

    def to_dict(self):
        """Return JSON-safe metadata."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create metadata from persisted data."""

        data = data or {}

        return ReferenceMetadata(
            data.get("author", ""),
            data.get("source_format", ""),
            data.get("created_at"),
            data.get("modified_at"),
        )


class ReferenceTransform:
    """Placement transform metadata for a reference instance."""

    def __init__(self, position=None, rotation=None, scale=None):

        self.position = position.copy() if position is not None else Vector3()
        self.rotation = rotation.copy() if rotation is not None else Vector3()
        self.scale = scale.copy() if scale is not None else Vector3(1.0, 1.0, 1.0)

    def to_dict(self):
        """Return JSON-safe transform data."""

        return {
            "position": _vector_to_data(self.position),
            "rotation": _vector_to_data(self.rotation),
            "scale": _vector_to_data(self.scale),
        }

    @staticmethod
    def from_dict(data):
        """Create transform data from persisted data."""

        data = data or {}

        return ReferenceTransform(
            _vector_from_data(data.get("position")),
            _vector_from_data(data.get("rotation")),
            _vector_from_data(data.get("scale") or {"x": 1.0, "y": 1.0, "z": 1.0}),
        )


class ReferenceModel:
    """External model reference definition."""

    def __init__(
        self,
        name="Reference Model",
        path="",
        reference_id=None,
        status="Loaded",
        visible=True,
        locked=False,
        category="General",
        group="Default",
    ):

        self.id = reference_id or str(uuid4())
        self.name = str(name)
        self.path = str(path)
        self.status = status if status in REFERENCE_STATUSES else "Loaded"
        self.visible = bool(visible)
        self.locked = bool(locked)
        self.category = category
        self.group = group
        self.metadata = ReferenceMetadata()
        self.reload_requested = False
        self.reader_type = ""
        self.import_settings = ImportSettings()
        self.import_statistics = ImportStatistics()
        self.import_metadata = {}
        self.import_warnings = []
        self.import_errors = []
        self.mesh_data = MeshData()
        self.layer_mappings = {"Default": ReferenceLayerMapping()}
        self.style_overrides = ReferenceStyleOverrides()
        self.display_presets = {}
        self.coordination_ui_settings = {
            "alignment": "WCS",
            "origin_mapping": "Model Origin",
            "coordinate_display": "WCS",
            "validation_status": "Unchecked",
            "conflict_placeholder": "",
        }

    def reload(self):
        """Mark the reference as reloaded without live synchronization."""

        self.status = "Loaded"
        self.reload_requested = False
        self.metadata.touch()

    def unload(self):
        """Unload this reference model."""

        self.status = "Unloaded"
        self.metadata.touch()

    def to_dict(self):
        """Return JSON-safe reference model data."""

        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "status": self.status,
            "visible": self.visible,
            "locked": self.locked,
            "category": self.category,
            "group": self.group,
            "metadata": self.metadata.to_dict(),
            "reload_requested": self.reload_requested,
            "reader_type": self.reader_type,
            "import_settings": self.import_settings.to_dict(),
            "import_statistics": self.import_statistics.to_dict(),
            "import_metadata": dict(self.import_metadata),
            "import_warnings": list(self.import_warnings),
            "import_errors": list(self.import_errors),
            "mesh_data": self.mesh_data.to_dict(),
            "layer_mappings": {
                name: mapping.to_dict()
                for name, mapping in self.layer_mappings.items()
            },
            "style_overrides": self.style_overrides.to_dict(),
            "display_presets": dict(self.display_presets),
            "coordination_ui_settings": dict(self.coordination_ui_settings),
        }

    @staticmethod
    def from_dict(data):
        """Create a reference model from persisted data."""

        data = data or {}
        model = ReferenceModel(
            data.get("name", "Reference Model"),
            data.get("path", ""),
            data.get("id"),
            data.get("status", "Loaded"),
            data.get("visible", True),
            data.get("locked", False),
            data.get("category", "General"),
            data.get("group", "Default"),
        )
        model.metadata = ReferenceMetadata.from_dict(data.get("metadata", {}))
        model.reload_requested = bool(data.get("reload_requested", False))
        model.reader_type = data.get("reader_type", "")
        model.import_settings = ImportSettings.from_dict(data.get("import_settings", {}))
        model.import_statistics = ImportStatistics.from_dict(data.get("import_statistics", {}))
        model.import_metadata = dict(data.get("import_metadata", {}))
        model.import_warnings = list(data.get("import_warnings", []))
        model.import_errors = list(data.get("import_errors", []))
        model.mesh_data = MeshData.from_dict(data.get("mesh_data", {}))
        model.layer_mappings = {
            name: ReferenceLayerMapping.from_dict(item)
            for name, item in (data.get("layer_mappings", {}) or {"Default": {}}).items()
        }
        model.style_overrides = ReferenceStyleOverrides.from_dict(data.get("style_overrides", {}))
        model.display_presets = dict(data.get("display_presets", {}))
        model.coordination_ui_settings = dict(data.get("coordination_ui_settings", model.coordination_ui_settings))

        return model

    def apply_import_result(self, result, settings=None):
        """Attach imported mesh data and metadata to this reference model."""

        self.reader_type = result.reader_type
        self.path = result.path
        self.status = "Loaded" if result.ok else "Error"
        self.import_settings = settings or self.import_settings
        self.import_statistics = result.statistics
        self.import_metadata = dict(result.metadata)
        self.import_warnings = list(result.warnings)
        self.import_errors = list(result.errors)
        self.mesh_data = result.mesh_data
        self.metadata.source_format = result.reader_type
        self.metadata.touch()
        self._ensure_default_layer_mapping()

    def visible_layer_mappings(self):
        """Return reference layers currently visible."""

        isolated = [
            mapping for mapping in self.layer_mappings.values()
            if mapping.isolated
        ]

        candidates = isolated or list(self.layer_mappings.values())

        return [mapping for mapping in candidates if mapping.visible]

    def has_visible_layer(self):
        """Return True when at least one mapped reference layer is visible."""

        return bool(self.visible_layer_mappings())

    def layers_locked(self):
        """Return True when all visible reference layers are locked."""

        visible = self.visible_layer_mappings()

        return bool(visible) and all(mapping.locked for mapping in visible)

    def _ensure_default_layer_mapping(self):

        if not self.layer_mappings:
            self.layer_mappings = {"Default": ReferenceLayerMapping()}


class ReferenceInstance:
    """Selectable 3D instance of an external reference model."""

    type_name = "ReferenceInstance"
    is_3d = True
    is_reference = True

    def __init__(self, model_id, name="Reference Instance", transform=None, size=100.0):

        self.id = str(uuid4())
        self.model_id = model_id
        self.name = str(name)
        self.transform = transform or ReferenceTransform()
        self.size = float(size)
        self.visible = True
        self.locked = False
        self.selected = False
        self.hovered = False
        self.layer = None
        self.layer_id = None
        self.layer_name = None
        self.color = "#90caf9"

    @property
    def bounding_box3d(self):
        """Return reference instance display bounds."""

        box = BoundingBox3D()

        for point in self.points():
            box.add(point)

        return box

    @property
    def display_color(self):
        """Return display color."""

        return self.color or "#90caf9"

    def points(self):
        """Return display bounds corners."""

        half = self.size * 0.5
        scale = self.transform.scale
        center = self.transform.position

        return [
            center + Vector3(x * scale.x, y * scale.y, z * scale.z)
            for x in (-half, half)
            for y in (-half, half)
            for z in (-half, half)
        ]

    def segments(self):
        """Return reference bounding wire segments."""

        corners = self.points()
        edges = [
            (0, 1), (0, 2), (0, 4), (3, 1),
            (3, 2), (3, 7), (5, 1), (5, 4),
            (5, 7), (6, 2), (6, 4), (6, 7),
        ]

        return [(corners[start], corners[end]) for start, end in edges]

    def to_dict(self):
        """Return JSON-safe instance data."""

        return {
            "id": self.id,
            "model_id": self.model_id,
            "name": self.name,
            "transform": self.transform.to_dict(),
            "size": self.size,
            "visible": self.visible,
            "locked": self.locked,
            "selected": self.selected,
            "layer_name": self.layer_name,
            "color": self.color,
        }

    @staticmethod
    def from_dict(data):
        """Create an instance from persisted data."""

        data = data or {}
        instance = ReferenceInstance(
            data.get("model_id"),
            data.get("name", "Reference Instance"),
            ReferenceTransform.from_dict(data.get("transform", {})),
            data.get("size", 100.0),
        )
        instance.id = data.get("id", instance.id)
        instance.visible = bool(data.get("visible", True))
        instance.locked = bool(data.get("locked", False))
        instance.selected = bool(data.get("selected", False))
        instance.layer_name = data.get("layer_name")
        instance.color = data.get("color", instance.color)

        return instance


class ReferenceManager:
    """Workspace-owned external reference manager."""

    def __init__(self):

        self.models = []
        self.instances = []
        self.isolated_model_ids = []

    def add_model(self, model):
        """Store a reference model."""

        if model not in self.models:
            model.name = self._unique_model_name(model.name, model)
            self.models.append(model)

        return model

    def create_model(self, name, path, **metadata):
        """Create a reference model."""

        model = ReferenceModel(name, path, category=metadata.get("category", "General"), group=metadata.get("group", "Default"))
        model.metadata.author = metadata.get("author", "")
        model.metadata.source_format = metadata.get("source_format", "")
        model.reader_type = metadata.get("reader_type", "")

        return self.add_model(model)

    def create_imported_model(self, result, name=None, settings=None, **metadata):
        """Create a reference model from an import result."""

        model = ReferenceModel(
            name or result.metadata.get("file_name") or "Imported Reference",
            result.path,
            status="Loaded" if result.ok else "Error",
            category=metadata.get("category", "Imported"),
            group=metadata.get("group", "Default"),
        )
        model.apply_import_result(result, settings or ImportSettings())

        return self.add_model(model)

    def remove_model(self, model):
        """Remove a reference model and its instances."""

        target = self.get_model(model)

        if target is None:
            return False

        self.models.remove(target)
        self.instances = [instance for instance in self.instances if instance.model_id != target.id]

        return True

    def add_instance(self, instance):
        """Store a reference instance."""

        if instance not in self.instances:
            self.instances.append(instance)

        return instance

    def create_instance(self, model, transform=None, name=None):
        """Create an instance for a reference model."""

        target = self.get_model(model)

        if target is None:
            return None

        return self.add_instance(ReferenceInstance(target.id, name or target.name, transform))

    def remove_instance(self, instance):
        """Remove an instance."""

        target = self.get_instance(instance)

        if target is None:
            return False

        self.instances.remove(target)

        return True

    def reload(self, model):
        """Reload a reference model placeholder."""

        target = self.get_model(model)

        if target is None:
            return False

        target.reload()

        return True

    def unload(self, model):
        """Unload a reference model placeholder."""

        target = self.get_model(model)

        if target is None:
            return False

        target.unload()

        return True

    def visible_instances(self):
        """Return visible instances respecting reference visibility and isolation."""

        isolated = set(self.isolated_model_ids)

        return [
            instance for instance in self.instances
            if (
                getattr(instance, "visible", True) and
                self._model_visible(instance.model_id) and
                (not isolated or instance.model_id in isolated)
            )
        ]

    def isolate(self, model):
        """Isolate a reference model."""

        target = self.get_model(model)

        if target is not None:
            self.isolated_model_ids = [target.id]

        return target

    def clear_isolation(self):
        """Clear reference isolation."""

        self.isolated_model_ids = []

    def reference_layer_mappings(self, model):
        """Return layer mappings for a reference model."""

        target = self.get_model(model)

        if target is None:
            return []

        target._ensure_default_layer_mapping()

        return list(target.layer_mappings.values())

    def update_layer_mapping(self, model, layer_name, **changes):
        """Update a reference layer mapping."""

        target = self.get_model(model)

        if target is None:
            return None

        target._ensure_default_layer_mapping()
        mapping = target.layer_mappings.get(layer_name)

        if mapping is None:
            mapping = ReferenceLayerMapping(layer_name)
            target.layer_mappings[layer_name] = mapping

        for key, value in changes.items():
            if hasattr(mapping, key):
                setattr(mapping, key, value)

        return mapping

    def layer_statistics(self, model=None):
        """Return reference layer statistics."""

        models = [self.get_model(model)] if model is not None else list(self.models)
        models = [item for item in models if item is not None]
        mappings = [
            mapping for item in models
            for mapping in self.reference_layer_mappings(item)
        ]

        return {
            "layers": len(mappings),
            "visible": len([mapping for mapping in mappings if mapping.visible]),
            "locked": len([mapping for mapping in mappings if mapping.locked]),
            "isolated": len([mapping for mapping in mappings if mapping.isolated]),
        }

    def update_style_overrides(self, model, **changes):
        """Update reference display style overrides."""

        target = self.get_model(model)

        if target is None:
            return None

        for key, value in changes.items():
            if hasattr(target.style_overrides, key):
                setattr(target.style_overrides, key, value)

        return target.style_overrides

    def save_display_preset(self, model, name):
        """Save the current reference style as a display preset."""

        target = self.get_model(model)

        if target is None:
            return None

        preset_name = str(name or "Preset")
        target.display_presets[preset_name] = target.style_overrides.to_dict()
        target.style_overrides.preset_name = preset_name

        return target.display_presets[preset_name]

    def apply_display_preset(self, model, name):
        """Apply a saved reference display preset."""

        target = self.get_model(model)

        if target is None:
            return None

        data = target.display_presets.get(name)

        if data is None:
            return None

        target.style_overrides = ReferenceStyleOverrides.from_dict(data)
        target.style_overrides.preset_name = name

        return target.style_overrides

    def search(self, text):
        """Search references by model name, path, category or group."""

        query = str(text or "").lower()

        return [
            model for model in self.models
            if (
                query in model.name.lower() or
                query in model.path.lower() or
                query in model.category.lower() or
                query in model.group.lower()
            )
        ]

    def filter(self, status=None, category=None, group=None):
        """Filter reference models."""

        return [
            model for model in self.models
            if (
                (status is None or model.status == status) and
                (category is None or model.category == category) and
                (group is None or model.group == group)
            )
        ]

    def statistics(self):
        """Return reference summary statistics."""

        return {
            "models": len(self.models),
            "instances": len(self.instances),
            "loaded": len([model for model in self.models if model.status == "Loaded"]),
            "unloaded": len([model for model in self.models if model.status == "Unloaded"]),
        }

    def get_model(self, model):
        """Return model by object, id, name or path."""

        if isinstance(model, ReferenceModel):
            return model if model in self.models else None

        for item in self.models:
            if item.id == model or item.name == model or item.path == model:
                return item

        return None

    def get_instance(self, instance):
        """Return instance by object, id or name."""

        if isinstance(instance, ReferenceInstance):
            return instance if instance in self.instances else None

        for item in self.instances:
            if item.id == instance or item.name == instance:
                return item

        return None

    def to_dict(self):
        """Return JSON-safe reference manager data."""

        return {
            "models": [model.to_dict() for model in self.models],
            "instances": [instance.to_dict() for instance in self.instances],
            "isolated_model_ids": list(self.isolated_model_ids),
        }

    def from_dict(self, data):
        """Restore reference manager data."""

        data = data or {}
        self.models = [ReferenceModel.from_dict(item) for item in data.get("models", [])]
        self.instances = [ReferenceInstance.from_dict(item) for item in data.get("instances", [])]
        self.isolated_model_ids = list(data.get("isolated_model_ids", []))

    def _model_visible(self, model_id):

        model = self.get_model(model_id)

        return (
            model is not None and
            model.visible and
            model.status == "Loaded" and
            model.has_visible_layer()
        )

    def _unique_model_name(self, name, current=None):

        base = str(name or "Reference Model").strip() or "Reference Model"
        names = {model.name for model in self.models if model is not current}

        if base not in names:
            return base

        index = 1

        while f"{base} {index}" in names:
            index += 1

        return f"{base} {index}"


class CoordinationRule:
    """Reusable coordination rule metadata."""

    def __init__(self, name="Coordination Rule", rule_type="Model Alignment", enabled=True, settings=None):

        self.id = str(uuid4())
        self.name = str(name)
        self.rule_type = rule_type
        self.enabled = bool(enabled)
        self.settings = dict(settings or {})

    def to_dict(self):
        """Return JSON-safe rule data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create a rule from persisted data."""

        data = data or {}
        rule = CoordinationRule(
            data.get("name", "Coordination Rule"),
            data.get("rule_type", "Model Alignment"),
            data.get("enabled", True),
            data.get("settings", {}),
        )
        rule.id = data.get("id", rule.id)

        return rule


class CoordinationManager:
    """Workspace-owned model coordination manager."""

    def __init__(self):

        self.rules = []
        self.shared_coordinate_system = "WCS"
        self.conflicts = []

    def add_rule(self, rule):
        """Store a coordination rule."""

        if rule not in self.rules:
            self.rules.append(rule)

        return rule

    def model_alignment(self, reference_id, target="WCS"):
        """Create a model alignment rule."""

        return self.add_rule(CoordinationRule("Model Alignment", "Model Alignment", settings={
            "reference_id": reference_id,
            "target": target,
        }))

    def origin_alignment(self, reference_id, origin=None):
        """Create an origin alignment rule."""

        return self.add_rule(CoordinationRule("Origin Alignment", "Origin Alignment", settings={
            "reference_id": reference_id,
            "origin": _vector_to_data(origin or Vector3()),
        }))

    def coordinate_mapping(self, source="WCS", target="WCS"):
        """Create a coordinate mapping rule."""

        return self.add_rule(CoordinationRule("Coordinate Mapping", "Coordinate Mapping", settings={
            "source": source,
            "target": target,
        }))

    def reference_offset(self, reference_id, offset=None):
        """Create a reference offset rule."""

        return self.add_rule(CoordinationRule("Reference Offset", "Reference Offset", settings={
            "reference_id": reference_id,
            "offset": _vector_to_data(offset or Vector3()),
        }))

    def reference_rotation(self, reference_id, rotation=None):
        """Create a reference rotation rule."""

        return self.add_rule(CoordinationRule("Reference Rotation", "Reference Rotation", settings={
            "reference_id": reference_id,
            "rotation": _vector_to_data(rotation or Vector3()),
        }))

    def reference_scale(self, reference_id, scale=None):
        """Create a reference scale rule."""

        return self.add_rule(CoordinationRule("Reference Scale", "Reference Scale", settings={
            "reference_id": reference_id,
            "scale": _vector_to_data(scale or Vector3(1.0, 1.0, 1.0)),
        }))

    def conflict_placeholder(self, description):
        """Store a future-ready clash/conflict placeholder."""

        conflict = {
            "id": str(uuid4()),
            "description": description,
            "status": "Placeholder",
            "created_at": _timestamp(),
        }
        self.conflicts.append(conflict)

        return conflict

    def to_dict(self):
        """Return JSON-safe coordination data."""

        return {
            "shared_coordinate_system": self.shared_coordinate_system,
            "rules": [rule.to_dict() for rule in self.rules],
            "conflicts": list(self.conflicts),
        }

    def from_dict(self, data):
        """Restore coordination data."""

        data = data or {}
        self.shared_coordinate_system = data.get("shared_coordinate_system", "WCS")
        self.rules = [CoordinationRule.from_dict(item) for item in data.get("rules", [])]
        self.conflicts = list(data.get("conflicts", []))


def _timestamp():

    return datetime.now(timezone.utc).isoformat()


def _vector_to_data(vector):

    return {"x": vector.x, "y": vector.y, "z": vector.z}


def _vector_from_data(data):

    data = data or {}

    return Vector3(data.get("x", 0.0), data.get("y", 0.0), data.get("z", 0.0))

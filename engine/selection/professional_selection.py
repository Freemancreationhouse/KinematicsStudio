from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SelectionMode(str, Enum):
    """Supported professional CAD selection modes."""

    OBJECT = "Object"
    BODY = "Body"
    FACE = "Face"
    EDGE = "Edge"
    VERTEX = "Vertex"
    LOOP = "Loop"
    RING = "Ring"
    SHELL = "Shell"
    COMPONENT = "Component"
    ASSEMBLY = "Assembly"


class SelectionFilterType(str, Enum):
    """Selection filter categories exposed to tools, UI and AI."""

    BODIES = "Bodies"
    FACES = "Faces"
    EDGES = "Edges"
    VERTICES = "Vertices"
    SKETCHES = "Sketches"
    CONSTRUCTION_GEOMETRY = "Construction Geometry"
    REFERENCE_GEOMETRY = "Reference Geometry"
    ASSEMBLIES = "Assemblies"
    ANNOTATIONS = "Annotations"
    DIMENSIONS = "Dimensions"
    CONSTRAINTS = "Constraints"


DEFAULT_SELECTION_PRIORITY: tuple[SelectionMode, ...] = (
    SelectionMode.VERTEX,
    SelectionMode.EDGE,
    SelectionMode.FACE,
    SelectionMode.BODY,
    SelectionMode.ASSEMBLY,
)


@dataclass(frozen=True)
class SelectionTarget:
    """Persistent reference metadata for one selected model item."""

    entity: Any
    mode: SelectionMode
    persistent_id: str
    topology_id: str = ""
    feature_id: str = ""
    layer_name: str = ""
    material_id: str = ""
    kind: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_entity(
        cls,
        entity: Any,
        mode: SelectionMode,
    ) -> "SelectionTarget":
        """Create a persistent selection target from an entity-like object."""

        persistent_id = _first_text(
            entity,
            (
                "persistent_topology_id",
                "topology_id",
                "persistent_id",
                "id",
                "name",
            ),
        )
        topology_id = _first_text(
            entity,
            ("topology_id", "persistent_topology_id", "topology_ref"),
        )
        feature_id = _first_text(entity, ("feature_id", "source_feature_id"))
        material_id = _first_text(entity, ("material_id", "material", "material_name"))
        layer_name = _first_text(entity, ("layer_name", "layer"))
        kind = _first_text(entity, ("selection_kind", "entity_type", "type"))
        return cls(
            entity=entity,
            mode=mode,
            persistent_id=persistent_id,
            topology_id=topology_id,
            feature_id=feature_id,
            layer_name=layer_name,
            material_id=material_id,
            kind=kind or entity.__class__.__name__,
            metadata={
                "class": entity.__class__.__name__,
                "locked": bool(getattr(entity, "locked", False)),
                "suppressed": bool(getattr(entity, "suppressed", False)),
            },
        )


@dataclass
class SelectionContext:
    """Read-only command availability context derived from selection state."""

    mode: SelectionMode = SelectionMode.OBJECT
    count: int = 0
    target_types: tuple[str, ...] = ()
    persistent_ids: tuple[str, ...] = ()
    available_command_groups: tuple[str, ...] = ()
    ai_request_types: tuple[str, ...] = ()

    def update(
        self,
        *,
        mode: SelectionMode,
        targets: Iterable[SelectionTarget],
    ) -> None:
        """Refresh this context from selected targets."""

        target_list = list(targets)
        self.mode = mode
        self.count = len(target_list)
        self.target_types = tuple(
            sorted({target.kind for target in target_list if target.kind})
        )
        self.persistent_ids = tuple(
            target.persistent_id
            for target in target_list
            if target.persistent_id
        )
        self.available_command_groups = self._command_groups_for(mode, target_list)
        self.ai_request_types = self._ai_request_types_for(mode)

    def _command_groups_for(
        self,
        mode: SelectionMode,
        targets: list[SelectionTarget],
    ) -> tuple[str, ...]:
        """Return command group names made relevant by this selection."""

        if not targets:
            return ()
        if mode == SelectionMode.VERTEX:
            return ("Vertex", "Measure", "Properties")
        if mode == SelectionMode.EDGE:
            return ("Edge", "Measure", "Properties")
        if mode in (SelectionMode.LOOP, SelectionMode.RING):
            return ("Loop", "Measure", "Properties")
        if mode == SelectionMode.FACE:
            return ("Face", "Material", "Measure", "Properties")
        if mode in (SelectionMode.BODY, SelectionMode.SHELL):
            return ("Body", "Material", "Measure", "Properties")
        if mode in (SelectionMode.COMPONENT, SelectionMode.ASSEMBLY):
            return ("Assembly", "Measure", "Properties")
        return ("Object", "Measure", "Properties")

    def _ai_request_types_for(self, mode: SelectionMode) -> tuple[str, ...]:
        """Return AI-safe selection request labels for the active mode."""

        mapping = {
            SelectionMode.BODY: ("Select Body", "Select Feature"),
            SelectionMode.FACE: ("Select Face", "Select Feature"),
            SelectionMode.EDGE: ("Select Edge", "Select Feature"),
            SelectionMode.VERTEX: ("Select Vertex", "Select Feature"),
            SelectionMode.OBJECT: ("Select Feature",),
        }
        return mapping.get(mode, ("Select Feature",))


class SelectionPolicy:
    """Configurable selection mode, filters and priority rules."""

    def __init__(self) -> None:
        """Create the default professional CAD selection policy."""

        self.mode = SelectionMode.OBJECT
        self.enabled_filters: set[SelectionFilterType] = set()
        self.priority: list[SelectionMode] = list(DEFAULT_SELECTION_PRIORITY)

    def set_mode(self, mode: SelectionMode | str) -> SelectionMode:
        """Set and return the active selection mode."""

        self.mode = normalize_selection_mode(mode)
        return self.mode

    def enable_filter(self, filter_type: SelectionFilterType | str) -> None:
        """Enable one selection filter."""

        self.enabled_filters.add(normalize_filter_type(filter_type))

    def disable_filter(self, filter_type: SelectionFilterType | str) -> None:
        """Disable one selection filter."""

        self.enabled_filters.discard(normalize_filter_type(filter_type))

    def clear_filters(self) -> None:
        """Disable all professional selection filters."""

        self.enabled_filters.clear()

    def set_priority(self, priority: Iterable[SelectionMode | str]) -> None:
        """Replace the selection priority order."""

        normalized = [normalize_selection_mode(item) for item in priority]
        if not normalized:
            raise ValueError("Selection priority must contain at least one mode.")
        self.priority = normalized

    def accepts(self, entity: Any, workspace: Any | None = None) -> bool:
        """Return True when an entity is selectable under this policy."""

        if not self._mode_accepts(entity, workspace):
            return False
        if not self.enabled_filters:
            return True
        return any(
            self._filter_accepts(filter_type, entity, workspace)
            for filter_type in self.enabled_filters
        )

    def _mode_accepts(self, entity: Any, workspace: Any | None) -> bool:
        """Return True when the active mode accepts an entity."""

        if self.mode == SelectionMode.OBJECT:
            return True
        return _matches_semantic_type(entity, self.mode.value, workspace)

    def _filter_accepts(
        self,
        filter_type: SelectionFilterType,
        entity: Any,
        workspace: Any | None,
    ) -> bool:
        """Return True when a professional filter accepts an entity."""

        return _matches_semantic_type(entity, filter_type.value, workspace)


def normalize_selection_mode(mode: SelectionMode | str) -> SelectionMode:
    """Normalize a string or enum into a SelectionMode."""

    if isinstance(mode, SelectionMode):
        return mode
    text = str(mode or "").strip()
    for candidate in SelectionMode:
        if text.lower() in {candidate.name.lower(), candidate.value.lower()}:
            return candidate
    raise ValueError(f"Unsupported selection mode: {mode!r}")


def normalize_filter_type(
    filter_type: SelectionFilterType | str,
) -> SelectionFilterType:
    """Normalize a string or enum into a SelectionFilterType."""

    if isinstance(filter_type, SelectionFilterType):
        return filter_type
    text = str(filter_type or "").strip()
    for candidate in SelectionFilterType:
        if text.lower() in {candidate.name.lower(), candidate.value.lower()}:
            return candidate
    raise ValueError(f"Unsupported selection filter: {filter_type!r}")


def resolve_persistent_id(entity: Any) -> str:
    """Return the best persistent identifier available for an entity."""

    return SelectionTarget.from_entity(entity, SelectionMode.OBJECT).persistent_id


def _matches_semantic_type(
    entity: Any,
    semantic_type: str,
    workspace: Any | None,
) -> bool:
    """Return True when an entity matches a semantic selection category."""

    terms = _entity_terms(entity, workspace)
    wanted = semantic_type.lower().replace(" ", "_")
    singular = wanted[:-1] if wanted.endswith("s") else wanted
    aliases = {
        "body": {"body", "solid", "mesh", "surface", "primitive", "entity3d"},
        "face": {"face", "surface"},
        "edge": {"edge", "curve", "line", "arc", "spline", "polyline"},
        "vertex": {"vertex", "point"},
        "sketch": {
            "sketch",
            "line",
            "arc",
            "circle",
            "ellipse",
            "spline",
            "polyline",
            "rectangle",
            "polygon",
        },
        "annotation": {
            "annotation",
            "text",
            "mtext",
            "leader",
            "dimension",
        },
        "dimension": {"dimension", "linear_dimension", "aligned_dimension"},
        "assembly": {"assembly", "assemblie"},
        "construction_geometry": {"construction", "construction_geometry"},
        "reference_geometry": {"reference", "reference_geometry"},
    }
    if terms.intersection(aliases.get(singular, set())):
        return True
    return wanted in terms or singular in terms


def _entity_terms(entity: Any, workspace: Any | None) -> set[str]:
    """Return normalized semantic labels known for an entity-like object."""

    values: list[Any] = [
        entity.__class__.__name__,
        getattr(entity, "selection_kind", ""),
        getattr(entity, "entity_type", ""),
        getattr(entity, "type", ""),
        getattr(entity, "kind", ""),
        getattr(entity, "category", ""),
    ]
    metadata = getattr(entity, "metadata", None)
    if isinstance(metadata, dict):
        values.extend(
            metadata.get(key, "")
            for key in ("selection_kind", "entity_type", "type", "category")
        )
    layer = getattr(entity, "layer_name", "")
    if layer:
        values.append(layer)
    if workspace is not None:
        entity_layer = getattr(workspace, "entity_layer", None)
        if callable(entity_layer):
            layer_obj = entity_layer(entity)
            values.append(getattr(layer_obj, "name", ""))
    terms: set[str] = set()
    for value in values:
        text = str(value or "")
        if not text:
            continue
        normalized = text.replace("Entity", "").replace("-", "_").replace(" ", "_")
        terms.add(normalized.lower())
        terms.add(normalized.lower().rstrip("s"))
    return terms


def _first_text(entity: Any, names: tuple[str, ...]) -> str:
    """Read the first non-empty text-like value from an object."""

    for name in names:
        value = getattr(entity, name, "")
        if callable(value):
            try:
                value = value()
            except TypeError:
                continue
        if value is None:
            continue
        text = str(value)
        if text:
            return text
    return ""

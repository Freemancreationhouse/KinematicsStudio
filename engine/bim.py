import dataclasses
from dataclasses import dataclass, field
from uuid import uuid4

from engine.geometry import BoundingBox3D, Vector3


@dataclass
class BuildingMetadata:
    """Descriptive metadata for a BIM project or building."""

    author: str = ""
    organization: str = ""
    project_number: str = ""
    address: str = ""
    phase: str = "Concept"

    def to_dict(self):
        """Return JSON-safe metadata."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create metadata from persisted data."""

        data = data or {}

        return BuildingMetadata(
            data.get("author", ""),
            data.get("organization", ""),
            data.get("project_number", ""),
            data.get("address", ""),
            data.get("phase", "Concept"),
        )


@dataclass
class BIMSettings:
    """Persistent BIM defaults and coordination settings."""

    units: str = "meters"
    default_level_height: float = 3.0
    grid_spacing: float = 10.0
    discipline: str = "Architecture"
    classification_system: str = "Uniclass"

    def to_dict(self):
        """Return JSON-safe settings."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create settings from persisted data."""

        data = data or {}

        return BIMSettings(
            data.get("units", "meters"),
            float(data.get("default_level_height", 3.0)),
            float(data.get("grid_spacing", 10.0)),
            data.get("discipline", "Architecture"),
            data.get("classification_system", "Uniclass"),
        )


class Site:
    """BIM site hierarchy item."""

    def __init__(self, name="Site", location=None, metadata=None):

        self.id = str(uuid4())
        self.name = name
        self.location = location or Vector3()
        self.metadata = dict(metadata or {})
        self.visible = True
        self.locked = False

    def to_dict(self):
        """Return JSON-safe site data."""

        return {
            "id": self.id,
            "name": self.name,
            "location": _vector_to_data(self.location),
            "metadata": dict(self.metadata),
            "visible": self.visible,
            "locked": self.locked,
        }

    @staticmethod
    def from_dict(data):
        """Create a site from persisted data."""

        data = data or {}
        site = Site(
            data.get("name", "Site"),
            _vector_from_data(data.get("location")),
            data.get("metadata", {}),
        )
        site.id = data.get("id", site.id)
        site.visible = bool(data.get("visible", True))
        site.locked = bool(data.get("locked", False))

        return site


class Building:
    """BIM building hierarchy item."""

    def __init__(self, name="Building", site_id="", metadata=None):

        self.id = str(uuid4())
        self.name = name
        self.site_id = site_id
        self.metadata = (
            metadata
            if isinstance(metadata, BuildingMetadata)
            else BuildingMetadata.from_dict(metadata or {})
        )
        self.visible = True
        self.locked = False

    def to_dict(self):
        """Return JSON-safe building data."""

        return {
            "id": self.id,
            "name": self.name,
            "site_id": self.site_id,
            "metadata": self.metadata.to_dict(),
            "visible": self.visible,
            "locked": self.locked,
        }

    @staticmethod
    def from_dict(data):
        """Create a building from persisted data."""

        data = data or {}
        building = Building(
            data.get("name", "Building"),
            data.get("site_id", ""),
            BuildingMetadata.from_dict(data.get("metadata", {})),
        )
        building.id = data.get("id", building.id)
        building.visible = bool(data.get("visible", True))
        building.locked = bool(data.get("locked", False))

        return building


class BIMMarker:
    """Selectable BIM hierarchy marker rendered by Renderer3D."""

    is_3d = True
    is_bim = True

    def __init__(self, name="BIM Marker"):

        self.id = str(uuid4())
        self.name = name
        self.visible = True
        self.locked = False
        self.selected = False
        self.hovered = False
        self.layer_name = None


class Level(BIMMarker):
    """BIM level reference plane."""

    type_name = "Level"

    def __init__(self, name="Level", elevation=0.0, height=3.0, building_id=""):

        super().__init__(name)
        self.elevation = float(elevation)
        self.height = float(height)
        self.building_id = building_id
        self.display_color = "#26c6da"

    @property
    def location(self):
        """Return representative level location."""

        return Vector3(0.0, 0.0, self.elevation)

    @property
    def bounding_box3d(self):
        """Return broad level plane bounds."""

        pad = 50.0
        box = BoundingBox3D()
        box.add(Vector3(-pad, -pad, self.elevation))
        box.add(Vector3(pad, pad, self.elevation))

        return box

    def points(self):
        """Return level representative points."""

        return [self.location]

    def segments(self):
        """Return level visualization segments."""

        pad = 50.0
        z = self.elevation

        return [
            (Vector3(-pad, -pad, z), Vector3(pad, -pad, z)),
            (Vector3(pad, -pad, z), Vector3(pad, pad, z)),
            (Vector3(pad, pad, z), Vector3(-pad, pad, z)),
            (Vector3(-pad, pad, z), Vector3(-pad, -pad, z)),
            (Vector3(-pad, 0.0, z), Vector3(pad, 0.0, z)),
            (Vector3(0.0, -pad, z), Vector3(0.0, pad, z)),
        ]

    def to_dict(self):
        """Return JSON-safe level data."""

        return _marker_data(self, {
            "elevation": self.elevation,
            "height": self.height,
            "building_id": self.building_id,
            "display_color": self.display_color,
        })

    @staticmethod
    def from_dict(data):
        """Create a level from persisted data."""

        data = data or {}
        level = Level(
            data.get("name", "Level"),
            float(data.get("elevation", 0.0)),
            float(data.get("height", 3.0)),
            data.get("building_id", ""),
        )
        _restore_marker(level, data)
        level.display_color = data.get("display_color", level.display_color)

        return level


class GridSystem(BIMMarker):
    """BIM structural grid visualization."""

    type_name = "GridSystem"

    def __init__(
        self,
        name="Grid System",
        building_id="",
        spacing=10.0,
        count_x=4,
        count_y=4,
        elevation=0.0,
    ):

        super().__init__(name)
        self.building_id = building_id
        self.spacing = float(spacing)
        self.count_x = int(count_x)
        self.count_y = int(count_y)
        self.elevation = float(elevation)
        self.display_color = "#90caf9"

    @property
    def location(self):
        """Return grid origin."""

        return Vector3()

    @property
    def bounding_box3d(self):
        """Return grid bounds."""

        box = BoundingBox3D()
        width = max(self.count_x, 1) * self.spacing
        height = max(self.count_y, 1) * self.spacing
        z = self.elevation
        box.add(Vector3(0.0, 0.0, z))
        box.add(Vector3(width, height, z))

        return box

    def points(self):
        """Return grid representative points."""

        return [self.location]

    def segments(self):
        """Return grid line segments."""

        segments = []
        z = self.elevation
        width = max(self.count_x - 1, 1) * self.spacing
        height = max(self.count_y - 1, 1) * self.spacing

        for index in range(max(self.count_x, 1)):
            x = index * self.spacing
            segments.append((Vector3(x, 0.0, z), Vector3(x, height, z)))

        for index in range(max(self.count_y, 1)):
            y = index * self.spacing
            segments.append((Vector3(0.0, y, z), Vector3(width, y, z)))

        return segments

    def to_dict(self):
        """Return JSON-safe grid data."""

        return _marker_data(self, {
            "building_id": self.building_id,
            "spacing": self.spacing,
            "count_x": self.count_x,
            "count_y": self.count_y,
            "elevation": self.elevation,
            "display_color": self.display_color,
        })

    @staticmethod
    def from_dict(data):
        """Create a grid system from persisted data."""

        data = data or {}
        grid = GridSystem(
            data.get("name", "Grid System"),
            data.get("building_id", ""),
            float(data.get("spacing", 10.0)),
            int(data.get("count_x", 4)),
            int(data.get("count_y", 4)),
            float(data.get("elevation", 0.0)),
        )
        _restore_marker(grid, data)
        grid.display_color = data.get("display_color", grid.display_color)

        return grid


@dataclass
class FamilyMetadata:
    """Descriptive metadata for reusable BIM families."""

    author: str = ""
    manufacturer: str = ""
    version: str = "1.2"
    description: str = ""
    classification: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe metadata."""

        return {
            "author": self.author,
            "manufacturer": self.manufacturer,
            "version": self.version,
            "description": self.description,
            "classification": dict(self.classification),
        }

    @staticmethod
    def from_dict(data):
        """Create family metadata from persisted data."""

        data = data or {}

        return FamilyMetadata(
            data.get("author", ""),
            data.get("manufacturer", ""),
            data.get("version", "1.2"),
            data.get("description", ""),
            dict(data.get("classification", {})),
        )


@dataclass
class FamilyStatistics:
    """Summary counts for one BIM family."""

    types: int = 0
    instances: int = 0
    property_sets: int = 0

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create family statistics from persisted data."""

        data = data or {}

        return FamilyStatistics(
            int(data.get("types", 0)),
            int(data.get("instances", 0)),
            int(data.get("property_sets", 0)),
        )


@dataclass
class FamilyCategory:
    """Family category metadata grouped under BIM categories."""

    name: str = "Generic"
    bim_category_id: str = ""
    discipline: str = "Architecture"
    description: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe family category data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create a family category from persisted data."""

        data = data or {}

        return FamilyCategory(
            data.get("name", "Generic"),
            data.get("bim_category_id", ""),
            data.get("discipline", "Architecture"),
            data.get("description", ""),
            data.get("id", str(uuid4())),
        )


class BIMFamily:
    """Reusable BIM family metadata that references existing geometry through instances."""

    type_name = "BIMFamily"

    def __init__(self, name="BIM Family", category_id="", metadata=None):

        self.id = str(uuid4())
        self.name = name
        self.category_id = category_id
        self.metadata = (
            metadata
            if isinstance(metadata, FamilyMetadata)
            else FamilyMetadata.from_dict(metadata or {})
        )
        self.statistics = FamilyStatistics()
        self.type_ids = []
        self.default_property_set_ids = []
        self.visible = True
        self.locked = False

    def refresh_statistics(self, project=None):
        """Refresh counts from a BIM project when available."""

        if project is None:
            self.statistics = FamilyStatistics(
                len(self.type_ids),
                self.statistics.instances,
                len(self.default_property_set_ids),
            )
            return self.statistics

        type_ids = [item.id for item in project.types if item.family_id == self.id]
        instance_count = len([
            item for item in project.instances
            if item.family_id == self.id or item.type_id in type_ids
        ])
        property_count = len([
            item for item in project.property_sets
            if item.owner_id in (self.id, *type_ids)
        ])
        self.type_ids = type_ids
        self.statistics = FamilyStatistics(len(type_ids), instance_count, property_count)

        return self.statistics

    def to_dict(self):
        """Return JSON-safe family data."""

        return {
            "id": self.id,
            "name": self.name,
            "category_id": self.category_id,
            "metadata": self.metadata.to_dict(),
            "statistics": self.statistics.to_dict(),
            "type_ids": list(self.type_ids),
            "default_property_set_ids": list(self.default_property_set_ids),
            "visible": self.visible,
            "locked": self.locked,
        }

    @staticmethod
    def from_dict(data):
        """Create a BIM family from persisted data."""

        data = data or {}
        family = BIMFamily(
            data.get("name", "BIM Family"),
            data.get("category_id", ""),
            FamilyMetadata.from_dict(data.get("metadata", {})),
        )
        family.id = data.get("id", family.id)
        family.statistics = FamilyStatistics.from_dict(data.get("statistics", {}))
        family.type_ids = list(data.get("type_ids", []))
        family.default_property_set_ids = list(data.get("default_property_set_ids", []))
        family.visible = bool(data.get("visible", True))
        family.locked = bool(data.get("locked", False))

        return family


class BIMFamilyLibrary:
    """Project-scoped BIM family lookup and organization helper."""

    def __init__(self, project=None):

        self.project = project

    @property
    def families(self):
        """Return project families."""

        return [] if self.project is None else self.project.families

    def add_family(self, family):
        """Store a BIM family."""

        if family not in self.families:
            self.families.append(family)

        return family

    def get_family(self, family):
        """Return a family by object, id or name."""

        if isinstance(family, BIMFamily):
            return family if family in self.families else None

        for item in self.families:
            if item.id == family or item.name == family:
                return item

        return None

    def remove_family(self, family):
        """Remove a family from the library."""

        target = self.get_family(family)

        if target is None:
            return False

        self.families.remove(target)
        return True

    def summary(self):
        """Return family library summary statistics."""

        return {
            "families": len(self.families),
            "types": sum(len(getattr(item, "type_ids", [])) for item in self.families),
        }


@dataclass
class TypeParameters:
    """Named BIM type parameters."""

    values: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe type parameters."""

        return dict(self.values)

    @staticmethod
    def from_dict(data):
        """Create type parameters from persisted data."""

        return TypeParameters(dict(data or {}))


@dataclass
class TypeDefaults:
    """Default instance values for a BIM type."""

    values: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe defaults."""

        return dict(self.values)

    @staticmethod
    def from_dict(data):
        """Create type defaults from persisted data."""

        return TypeDefaults(dict(data or {}))


@dataclass
class InstanceParameters:
    """Instance-specific BIM parameters."""

    values: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe instance parameters."""

        return dict(self.values)

    @staticmethod
    def from_dict(data):
        """Create instance parameters from persisted data."""

        return InstanceParameters(dict(data or {}))


@dataclass
class InstanceOverrides:
    """Instance overrides for type defaults."""

    values: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe instance overrides."""

        return dict(self.values)

    @staticmethod
    def from_dict(data):
        """Create instance overrides from persisted data."""

        return InstanceOverrides(dict(data or {}))


@dataclass
class PropertyDefinition:
    """Definition for a BIM property value."""

    name: str = ""
    data_type: str = "Text"
    unit: str = ""
    description: str = ""
    ifc_name: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe definition data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create a property definition from persisted data."""

        data = data or {}

        return PropertyDefinition(
            data.get("name", ""),
            data.get("data_type", "Text"),
            data.get("unit", ""),
            data.get("description", ""),
            data.get("ifc_name", ""),
            data.get("id", str(uuid4())),
        )


@dataclass
class PropertyValue:
    """Value for one BIM property definition."""

    definition_id: str = ""
    value: object = ""
    source: str = "Custom"
    overridden: bool = False

    def to_dict(self):
        """Return JSON-safe value data."""

        return {
            "definition_id": self.definition_id,
            "value": self.value,
            "source": self.source,
            "overridden": self.overridden,
        }

    @staticmethod
    def from_dict(data):
        """Create a property value from persisted data."""

        data = data or {}

        return PropertyValue(
            data.get("definition_id", ""),
            data.get("value", ""),
            data.get("source", "Custom"),
            bool(data.get("overridden", False)),
        )


@dataclass
class PropertyGroup:
    """Logical group of BIM property definitions."""

    name: str = "General"
    definition_ids: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe group data."""

        return {
            "id": self.id,
            "name": self.name,
            "definition_ids": list(self.definition_ids),
        }

    @staticmethod
    def from_dict(data):
        """Create a property group from persisted data."""

        data = data or {}

        return PropertyGroup(
            data.get("name", "General"),
            list(data.get("definition_ids", [])),
            data.get("id", str(uuid4())),
        )


class PropertySet:
    """Custom and IFC-ready BIM property set."""

    def __init__(self, name="Property Set", owner_id="", ifc_name="", classification=None):

        self.id = str(uuid4())
        self.name = name
        self.owner_id = owner_id
        self.ifc_name = ifc_name
        self.classification = dict(classification or {})
        self.definitions = []
        self.values = []
        self.groups = []

    def add_property(self, definition, value=None):
        """Add a definition and optional value to this set."""

        if definition not in self.definitions:
            self.definitions.append(definition)

        if value is not None and value not in self.values:
            self.values.append(value)

        return definition

    def value_for(self, name):
        """Return a property value by definition name."""

        definition = next((item for item in self.definitions if item.name == name), None)

        if definition is None:
            return None

        return next(
            (
                value for value in self.values
                if value.definition_id == definition.id
            ),
            None,
        )

    def to_dict(self):
        """Return JSON-safe property set data."""

        return {
            "id": self.id,
            "name": self.name,
            "owner_id": self.owner_id,
            "ifc_name": self.ifc_name,
            "classification": dict(self.classification),
            "definitions": [item.to_dict() for item in self.definitions],
            "values": [item.to_dict() for item in self.values],
            "groups": [item.to_dict() for item in self.groups],
        }

    @staticmethod
    def from_dict(data):
        """Create a property set from persisted data."""

        data = data or {}
        property_set = PropertySet(
            data.get("name", "Property Set"),
            data.get("owner_id", ""),
            data.get("ifc_name", ""),
            data.get("classification", {}),
        )
        property_set.id = data.get("id", property_set.id)
        property_set.definitions = [
            PropertyDefinition.from_dict(item)
            for item in data.get("definitions", [])
        ]
        property_set.values = [
            PropertyValue.from_dict(item)
            for item in data.get("values", [])
        ]
        property_set.groups = [
            PropertyGroup.from_dict(item)
            for item in data.get("groups", [])
        ]

        return property_set


ELEMENT_KINDS = (
    "Wall",
    "Door",
    "Window",
    "Column",
    "Beam",
    "Slab",
    "Roof",
    "Stair",
    "Railing",
    "Floor",
    "Ceiling",
    "Curtain Wall",
    "Foundation",
    "Opening",
    "Room",
    "Space",
    "Zone",
)


@dataclass
class ElementMetadata:
    """Professional BIM element metadata."""

    description: str = ""
    material: str = ""
    fire_rating: str = ""
    thermal: str = ""
    acoustic: str = ""
    manufacturer: str = ""
    model: str = ""
    cost: str = ""
    classification: dict = field(default_factory=dict)
    custom: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe element metadata."""

        return {
            "description": self.description,
            "material": self.material,
            "fire_rating": self.fire_rating,
            "thermal": self.thermal,
            "acoustic": self.acoustic,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "cost": self.cost,
            "classification": dict(self.classification),
            "custom": dict(self.custom),
        }

    @staticmethod
    def from_dict(data):
        """Create element metadata from persisted data."""

        data = data or {}

        return ElementMetadata(
            data.get("description", ""),
            data.get("material", ""),
            data.get("fire_rating", ""),
            data.get("thermal", ""),
            data.get("acoustic", ""),
            data.get("manufacturer", ""),
            data.get("model", ""),
            data.get("cost", ""),
            dict(data.get("classification", {})),
            dict(data.get("custom", {})),
        )


@dataclass
class ElementCategoryMetadata:
    """Category metadata for BIM element definitions."""

    name: str = "Generic"
    description: str = ""
    color: str = "#80cbc4"
    classification: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe category metadata."""

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "classification": dict(self.classification),
        }

    @staticmethod
    def from_dict(data):
        """Create category metadata from persisted data."""

        data = data or {}

        return ElementCategoryMetadata(
            data.get("name", "Generic"),
            data.get("description", ""),
            data.get("color", "#80cbc4"),
            dict(data.get("classification", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class LibraryStatistics:
    """Element library summary counts."""

    definitions: int = 0
    categories: int = 0
    instances: int = 0
    relationships: int = 0

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create statistics from persisted data."""

        data = data or {}

        return LibraryStatistics(
            int(data.get("definitions", 0)),
            int(data.get("categories", 0)),
            int(data.get("instances", 0)),
            int(data.get("relationships", 0)),
        )


@dataclass
class ElementParameters:
    """Common BIM element parameters and custom values."""

    name: str = ""
    description: str = ""
    category: str = ""
    type_name: str = ""
    material: str = ""
    fire_rating: str = ""
    thermal: str = ""
    acoustic: str = ""
    load_bearing: bool = False
    structural: bool = False
    manufacturer: str = ""
    model: str = ""
    cost: str = ""
    classification: dict = field(default_factory=dict)
    custom: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe element parameters."""

        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "type_name": self.type_name,
            "material": self.material,
            "fire_rating": self.fire_rating,
            "thermal": self.thermal,
            "acoustic": self.acoustic,
            "load_bearing": self.load_bearing,
            "structural": self.structural,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "cost": self.cost,
            "classification": dict(self.classification),
            "custom": dict(self.custom),
        }

    @staticmethod
    def from_dict(data):
        """Create element parameters from persisted data."""

        data = data or {}

        return ElementParameters(
            data.get("name", ""),
            data.get("description", ""),
            data.get("category", ""),
            data.get("type_name", ""),
            data.get("material", ""),
            data.get("fire_rating", ""),
            data.get("thermal", ""),
            data.get("acoustic", ""),
            bool(data.get("load_bearing", False)),
            bool(data.get("structural", False)),
            data.get("manufacturer", ""),
            data.get("model", ""),
            data.get("cost", ""),
            dict(data.get("classification", {})),
            dict(data.get("custom", {})),
        )


@dataclass
class ElementRelationships:
    """Relationship buckets for BIM element instances."""

    hosts: list = field(default_factory=list)
    parents: list = field(default_factory=list)
    children: list = field(default_factory=list)
    contained: list = field(default_factory=list)
    adjacent: list = field(default_factory=list)
    connections: list = field(default_factory=list)

    def to_dict(self):
        """Return JSON-safe relationship data."""

        return {
            "hosts": list(self.hosts),
            "parents": list(self.parents),
            "children": list(self.children),
            "contained": list(self.contained),
            "adjacent": list(self.adjacent),
            "connections": list(self.connections),
        }

    @staticmethod
    def from_dict(data):
        """Create element relationships from persisted data."""

        data = data or {}

        return ElementRelationships(
            list(data.get("hosts", [])),
            list(data.get("parents", [])),
            list(data.get("children", [])),
            list(data.get("contained", [])),
            list(data.get("adjacent", [])),
            list(data.get("connections", [])),
        )

    def related_ids(self):
        """Return all related object identifiers."""

        related = []

        for values in self.to_dict().values():
            related.extend(values)

        return related


class BIMElementDefinition:
    """Reusable professional BIM element definition."""

    type_name = "BIMElementDefinition"

    def __init__(self, kind="Wall", name=None, category_id="", metadata=None, parameters=None):

        self.id = str(uuid4())
        self.kind = kind if kind in ELEMENT_KINDS else "Wall"
        self.name = name or self.kind
        self.category_id = category_id
        self.metadata = (
            metadata
            if isinstance(metadata, ElementMetadata)
            else ElementMetadata.from_dict(metadata or {})
        )
        self.parameters = (
            parameters
            if isinstance(parameters, ElementParameters)
            else ElementParameters.from_dict(parameters or {})
        )
        self.type_ids = []
        self.property_set_ids = []
        self.visible = True
        self.locked = False

    def to_dict(self):
        """Return JSON-safe element definition data."""

        return {
            "id": self.id,
            "kind": self.kind,
            "name": self.name,
            "category_id": self.category_id,
            "metadata": self.metadata.to_dict(),
            "parameters": self.parameters.to_dict(),
            "type_ids": list(self.type_ids),
            "property_set_ids": list(self.property_set_ids),
            "visible": self.visible,
            "locked": self.locked,
        }

    @staticmethod
    def from_dict(data):
        """Create an element definition from persisted data."""

        data = data or {}
        definition = BIMElementDefinition(
            data.get("kind", "Wall"),
            data.get("name"),
            data.get("category_id", ""),
            ElementMetadata.from_dict(data.get("metadata", {})),
            ElementParameters.from_dict(data.get("parameters", {})),
        )
        definition.id = data.get("id", definition.id)
        definition.type_ids = list(data.get("type_ids", []))
        definition.property_set_ids = list(data.get("property_set_ids", []))
        definition.visible = bool(data.get("visible", True))
        definition.locked = bool(data.get("locked", False))

        return definition


class BIMElementLibrary:
    """Project-scoped professional BIM element definition library."""

    def __init__(self, project=None):

        self.project = project

    @property
    def definitions(self):
        """Return element definitions."""

        return [] if self.project is None else self.project.element_definitions

    def add_definition(self, definition):
        """Store an element definition."""

        if definition not in self.definitions:
            self.definitions.append(definition)

        return definition

    def get_definition(self, definition):
        """Return an element definition by object, id, name or kind."""

        if isinstance(definition, BIMElementDefinition):
            return definition if definition in self.definitions else None

        for item in self.definitions:
            if item.id == definition or item.name == definition or item.kind == definition:
                return item

        return None

    def remove_definition(self, definition):
        """Remove an element definition."""

        target = self.get_definition(definition)

        if target is None:
            return False

        self.definitions.remove(target)

        return True

    def statistics(self):
        """Return element library statistics."""

        if self.project is None:
            return LibraryStatistics()

        relationships = sum(
            len(getattr(item, "element_relationships", ElementRelationships()).related_ids())
            for item in self.project.instances
        )

        return LibraryStatistics(
            len(self.project.element_definitions),
            len(self.project.element_categories),
            len([
                item for item in self.project.instances
                if getattr(item, "element_definition_id", "")
            ]),
            relationships,
        )


@dataclass
class MaterialMetadata:
    """Professional BIM material metadata."""

    description: str = ""
    manufacturer: str = ""
    cost: str = ""
    physical: dict = field(default_factory=dict)
    appearance: dict = field(default_factory=dict)
    thermal: dict = field(default_factory=dict)
    structural: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe material metadata."""

        return {
            "description": self.description,
            "manufacturer": self.manufacturer,
            "cost": self.cost,
            "physical": dict(self.physical),
            "appearance": dict(self.appearance),
            "thermal": dict(self.thermal),
            "structural": dict(self.structural),
        }

    @staticmethod
    def from_dict(data):
        """Create material metadata from persisted data."""

        data = data or {}

        return MaterialMetadata(
            data.get("description", ""),
            data.get("manufacturer", ""),
            data.get("cost", ""),
            dict(data.get("physical", {})),
            dict(data.get("appearance", {})),
            dict(data.get("thermal", {})),
            dict(data.get("structural", {})),
        )


@dataclass
class MaterialCategory:
    """Material category metadata."""

    name: str = "Generic"
    description: str = ""
    color: str = "#a5d6a7"
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe category data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create material category from persisted data."""

        data = data or {}

        return MaterialCategory(
            data.get("name", "Generic"),
            data.get("description", ""),
            data.get("color", "#a5d6a7"),
            data.get("id", str(uuid4())),
        )


@dataclass
class MaterialStatistics:
    """Material library and assignment summary."""

    materials: int = 0
    categories: int = 0
    assignments: int = 0
    layer_sets: int = 0

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create statistics from persisted data."""

        data = data or {}

        return MaterialStatistics(
            int(data.get("materials", 0)),
            int(data.get("categories", 0)),
            int(data.get("assignments", 0)),
            int(data.get("layer_sets", 0)),
        )


@dataclass
class MaterialAsset:
    """Future-ready material asset placeholder."""

    asset_type: str = "Appearance"
    data: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe asset data."""

        return {"id": self.id, "asset_type": self.asset_type, "data": dict(self.data)}

    @staticmethod
    def from_dict(data):
        """Create material asset data."""

        data = data or {}

        return MaterialAsset(
            data.get("asset_type", "Appearance"),
            dict(data.get("data", {})),
            data.get("id", str(uuid4())),
        )


class BIMMaterial:
    """Reusable BIM material definition."""

    type_name = "BIMMaterial"

    def __init__(self, name="Material", category_id="", color="#a5d6a7", metadata=None):

        self.id = str(uuid4())
        self.name = name
        self.category_id = category_id
        self.color = color
        self.metadata = (
            metadata
            if isinstance(metadata, MaterialMetadata)
            else MaterialMetadata.from_dict(metadata or {})
        )
        self.property_set_ids = []
        self.assets = []
        self.visible = True
        self.locked = False

    def to_dict(self):
        """Return JSON-safe material data."""

        return {
            "id": self.id,
            "name": self.name,
            "category_id": self.category_id,
            "color": self.color,
            "metadata": self.metadata.to_dict(),
            "property_set_ids": list(self.property_set_ids),
            "assets": [asset.to_dict() for asset in self.assets],
            "visible": self.visible,
            "locked": self.locked,
        }

    @staticmethod
    def from_dict(data):
        """Create a BIM material from persisted data."""

        data = data or {}
        material = BIMMaterial(
            data.get("name", "Material"),
            data.get("category_id", ""),
            data.get("color", "#a5d6a7"),
            MaterialMetadata.from_dict(data.get("metadata", {})),
        )
        material.id = data.get("id", material.id)
        material.property_set_ids = list(data.get("property_set_ids", []))
        material.assets = [MaterialAsset.from_dict(item) for item in data.get("assets", [])]
        material.visible = bool(data.get("visible", True))
        material.locked = bool(data.get("locked", False))

        return material


@dataclass
class MaterialAssignment:
    """Assignment of a material to a BIM instance, type, family or assembly."""

    target_id: str = ""
    material_id: str = ""
    quantity: float = 1.0
    unit: str = "item"
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe assignment data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create a material assignment from persisted data."""

        data = data or {}

        return MaterialAssignment(
            data.get("target_id", ""),
            data.get("material_id", ""),
            float(data.get("quantity", 1.0)),
            data.get("unit", "item"),
            data.get("id", str(uuid4())),
        )


@dataclass
class MaterialLayer:
    """Layer within a composite material layer set."""

    material_id: str = ""
    thickness: float = 0.0
    function: str = "Finish"
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe layer data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create material layer data."""

        data = data or {}

        return MaterialLayer(
            data.get("material_id", ""),
            float(data.get("thickness", 0.0)),
            data.get("function", "Finish"),
            data.get("id", str(uuid4())),
        )


class MaterialLayerSet:
    """Composite layer set for walls, floors, roofs and assemblies."""

    def __init__(self, name="Material Layer Set", layers=None):

        self.id = str(uuid4())
        self.name = name
        self.layers = list(layers or [])

    @property
    def total_thickness(self):
        """Return combined layer thickness."""

        return sum(layer.thickness for layer in self.layers)

    def to_dict(self):
        """Return JSON-safe layer set data."""

        return {
            "id": self.id,
            "name": self.name,
            "layers": [layer.to_dict() for layer in self.layers],
        }

    @staticmethod
    def from_dict(data):
        """Create material layer set data."""

        data = data or {}
        layer_set = MaterialLayerSet(
            data.get("name", "Material Layer Set"),
            [MaterialLayer.from_dict(item) for item in data.get("layers", [])],
        )
        layer_set.id = data.get("id", layer_set.id)

        return layer_set


class MaterialLibrary:
    """Project-scoped BIM material library helper."""

    def __init__(self, project=None):

        self.project = project

    def add_material(self, material):
        """Store a BIM material."""

        if material not in self.project.materials:
            self.project.materials.append(material)

        return material

    def get_material(self, material):
        """Return a material by object, id or name."""

        if isinstance(material, BIMMaterial):
            return material if material in self.project.materials else None

        for item in self.project.materials:
            if item.id == material or item.name == material:
                return item

        return None

    def statistics(self):
        """Return material library statistics."""

        return MaterialStatistics(
            len(self.project.materials),
            len(self.project.material_categories),
            len(self.project.material_assignments),
            len(self.project.material_layer_sets),
        )


@dataclass
class AssemblyMetadata:
    """Assembly metadata for reusable BIM groupings."""

    description: str = ""
    author: str = ""
    version: str = "1.2"
    classification: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe assembly metadata."""

        return {
            "description": self.description,
            "author": self.author,
            "version": self.version,
            "classification": dict(self.classification),
        }

    @staticmethod
    def from_dict(data):
        """Create assembly metadata from persisted data."""

        data = data or {}

        return AssemblyMetadata(
            data.get("description", ""),
            data.get("author", ""),
            data.get("version", "1.2"),
            dict(data.get("classification", {})),
        )


@dataclass
class AssemblyStatistics:
    """Assembly member and nesting statistics."""

    members: int = 0
    nested: int = 0
    templates: int = 0

    def to_dict(self):
        """Return JSON-safe assembly statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create assembly statistics from persisted data."""

        data = data or {}

        return AssemblyStatistics(
            int(data.get("members", 0)),
            int(data.get("nested", 0)),
            int(data.get("templates", 0)),
        )


@dataclass
class AssemblyMember:
    """Reference to an existing BIM instance or nested assembly."""

    reference_id: str = ""
    role: str = "Member"
    quantity: float = 1.0
    reference_type: str = "BIMInstance"
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe member data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create assembly member data."""

        data = data or {}

        return AssemblyMember(
            data.get("reference_id", ""),
            data.get("role", "Member"),
            float(data.get("quantity", 1.0)),
            data.get("reference_type", "BIMInstance"),
            data.get("id", str(uuid4())),
        )


class AssemblyType:
    """Reusable assembly type or template definition."""

    def __init__(self, name="Assembly Type", template=False, metadata=None):

        self.id = str(uuid4())
        self.name = name
        self.template = bool(template)
        self.metadata = (
            metadata
            if isinstance(metadata, AssemblyMetadata)
            else AssemblyMetadata.from_dict(metadata or {})
        )

    def to_dict(self):
        """Return JSON-safe assembly type data."""

        return {
            "id": self.id,
            "name": self.name,
            "template": self.template,
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create an assembly type from persisted data."""

        data = data or {}
        assembly_type = AssemblyType(
            data.get("name", "Assembly Type"),
            bool(data.get("template", False)),
            AssemblyMetadata.from_dict(data.get("metadata", {})),
        )
        assembly_type.id = data.get("id", assembly_type.id)

        return assembly_type


class Assembly:
    """Reusable BIM assembly that references existing BIM instances."""

    type_name = "Assembly"

    def __init__(self, name="Assembly", assembly_type_id="", metadata=None):

        self.id = str(uuid4())
        self.name = name
        self.assembly_type_id = assembly_type_id
        self.metadata = (
            metadata
            if isinstance(metadata, AssemblyMetadata)
            else AssemblyMetadata.from_dict(metadata or {})
        )
        self.members = []
        self.relationships = {}
        self.statistics = AssemblyStatistics()
        self.visible = True
        self.locked = False
        self.selected = False

    def add_member(self, member):
        """Add a member reference to this assembly."""

        if member not in self.members:
            self.members.append(member)
            self.refresh_statistics()

        return member

    def refresh_statistics(self):
        """Refresh assembly statistics."""

        self.statistics = AssemblyStatistics(
            len(self.members),
            len([item for item in self.members if item.reference_type == "Assembly"]),
            0,
        )

        return self.statistics

    def to_dict(self):
        """Return JSON-safe assembly data."""

        return {
            "id": self.id,
            "name": self.name,
            "assembly_type_id": self.assembly_type_id,
            "metadata": self.metadata.to_dict(),
            "members": [member.to_dict() for member in self.members],
            "relationships": dict(self.relationships),
            "statistics": self.statistics.to_dict(),
            "visible": self.visible,
            "locked": self.locked,
            "selected": self.selected,
        }

    @staticmethod
    def from_dict(data):
        """Create assembly data from persistence."""

        data = data or {}
        assembly = Assembly(
            data.get("name", "Assembly"),
            data.get("assembly_type_id", ""),
            AssemblyMetadata.from_dict(data.get("metadata", {})),
        )
        assembly.id = data.get("id", assembly.id)
        assembly.members = [AssemblyMember.from_dict(item) for item in data.get("members", [])]
        assembly.relationships = dict(data.get("relationships", {}))
        assembly.statistics = AssemblyStatistics.from_dict(data.get("statistics", {}))
        assembly.visible = bool(data.get("visible", True))
        assembly.locked = bool(data.get("locked", False))
        assembly.selected = bool(data.get("selected", False))

        return assembly


class CompositeAssembly(Assembly):
    """Nested or composite BIM assembly."""

    type_name = "CompositeAssembly"


@dataclass
class QuantityRule:
    """Future-ready quantity rule."""

    name: str = "Default Quantity Rule"
    quantity_type: str = "Count"
    target: str = "BIMInstance"
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe rule data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create quantity rule from persisted data."""

        data = data or {}

        return QuantityRule(
            data.get("name", "Default Quantity Rule"),
            data.get("quantity_type", "Count"),
            data.get("target", "BIMInstance"),
            data.get("id", str(uuid4())),
        )


@dataclass
class QuantityItem:
    """One quantity takeoff result item."""

    source_id: str = ""
    source_name: str = ""
    quantity_type: str = "Count"
    value: float = 0.0
    unit: str = "item"
    material_id: str = ""
    assembly_id: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe quantity data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create quantity item from persisted data."""

        data = data or {}

        return QuantityItem(
            data.get("source_id", ""),
            data.get("source_name", ""),
            data.get("quantity_type", "Count"),
            float(data.get("value", 0.0)),
            data.get("unit", "item"),
            data.get("material_id", ""),
            data.get("assembly_id", ""),
            data.get("id", str(uuid4())),
        )


@dataclass
class QuantityStatistics:
    """Summary counts for quantity takeoff results."""

    items: int = 0
    total_count: float = 0.0
    total_length: float = 0.0
    total_area: float = 0.0
    total_volume: float = 0.0
    total_cost: float = 0.0

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create quantity statistics from persisted data."""

        data = data or {}

        return QuantityStatistics(
            int(data.get("items", 0)),
            float(data.get("total_count", 0.0)),
            float(data.get("total_length", 0.0)),
            float(data.get("total_area", 0.0)),
            float(data.get("total_volume", 0.0)),
            float(data.get("total_cost", 0.0)),
        )


@dataclass
class QuantitySummary:
    """Quantity takeoff summary."""

    by_type: dict = field(default_factory=dict)
    by_material: dict = field(default_factory=dict)
    by_assembly: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe summary data."""

        return {
            "by_type": dict(self.by_type),
            "by_material": dict(self.by_material),
            "by_assembly": dict(self.by_assembly),
        }

    @staticmethod
    def from_dict(data):
        """Create quantity summary data."""

        data = data or {}

        return QuantitySummary(
            dict(data.get("by_type", {})),
            dict(data.get("by_material", {})),
            dict(data.get("by_assembly", {})),
        )


class QuantityManager:
    """Project-scoped quantity takeoff helper using existing BIM data."""

    def __init__(self, project=None):

        self.project = project

    def run(self):
        """Aggregate quantities from BIM instances, materials and assemblies."""

        if self.project is None:
            return []

        items = []

        for instance in self.project.instances:
            items.extend(_instance_quantities(instance))

        for assignment in self.project.material_assignments:
            material = _find_by_id(self.project.materials, assignment.material_id)
            target = _find_by_id(self.project.instances, assignment.target_id)
            items.append(QuantityItem(
                assignment.target_id,
                getattr(target, "name", assignment.target_id),
                "Material",
                assignment.quantity,
                assignment.unit,
                assignment.material_id,
            ))
            if material is not None:
                items[-1].source_name = f"{items[-1].source_name} / {material.name}"

        for assembly in self.project.assemblies:
            items.append(QuantityItem(
                assembly.id,
                assembly.name,
                "Assembly",
                len(assembly.members),
                "member",
                "",
                assembly.id,
            ))

        self.project.quantity_items = items
        self.project.quantity_summary = self.summary(items)
        self.project.quantity_statistics = self.statistics(items)

        return items

    def summary(self, items=None):
        """Return quantity summary buckets."""

        items = list(items if items is not None else self.project.quantity_items)
        summary = QuantitySummary()

        for item in items:
            summary.by_type[item.quantity_type] = summary.by_type.get(item.quantity_type, 0.0) + item.value
            if item.material_id:
                summary.by_material[item.material_id] = summary.by_material.get(item.material_id, 0.0) + item.value
            if item.assembly_id:
                summary.by_assembly[item.assembly_id] = summary.by_assembly.get(item.assembly_id, 0.0) + item.value

        return summary

    def statistics(self, items=None):
        """Return quantity statistics."""

        items = list(items if items is not None else self.project.quantity_items)

        return QuantityStatistics(
            len(items),
            sum(item.value for item in items if item.quantity_type == "Count"),
            sum(item.value for item in items if item.quantity_type == "Length"),
            sum(item.value for item in items if item.quantity_type == "Area"),
            sum(item.value for item in items if item.quantity_type == "Volume"),
            sum(item.value for item in items if item.quantity_type == "Cost"),
        )


@dataclass
class LevelDefinition:
    """Professional BIM level definition referencing an existing Level marker."""

    name: str = "Level"
    level_id: str = ""
    elevation: float = 0.0
    visible: bool = True
    locked: bool = False
    metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe level definition data."""

        return {
            "id": self.id,
            "name": self.name,
            "level_id": self.level_id,
            "elevation": self.elevation,
            "visible": self.visible,
            "locked": self.locked,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create level definition from persisted data."""

        data = data or {}

        return LevelDefinition(
            data.get("name", "Level"),
            data.get("level_id", ""),
            float(data.get("elevation", 0.0)),
            bool(data.get("visible", True)),
            bool(data.get("locked", False)),
            dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class LevelGroup:
    """Named grouping of BIM levels."""

    name: str = "Level Group"
    level_ids: list = field(default_factory=list)
    visible: bool = True
    locked: bool = False
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe level group data."""

        return {
            "id": self.id,
            "name": self.name,
            "level_ids": list(self.level_ids),
            "visible": self.visible,
            "locked": self.locked,
        }

    @staticmethod
    def from_dict(data):
        """Create level group from persisted data."""

        data = data or {}

        return LevelGroup(
            data.get("name", "Level Group"),
            list(data.get("level_ids", [])),
            bool(data.get("visible", True)),
            bool(data.get("locked", False)),
            data.get("id", str(uuid4())),
        )


class LevelManager:
    """Project-scoped professional BIM level helper."""

    def __init__(self, project=None):

        self.project = project

    def add_definition(self, definition):
        """Store a level definition."""

        if definition not in self.project.level_definitions:
            self.project.level_definitions.append(definition)

        return definition

    def add_group(self, group):
        """Store a level group."""

        if group not in self.project.level_groups:
            self.project.level_groups.append(group)

        return group

    def statistics(self):
        """Return level statistics."""

        return {
            "levels": len(self.project.levels),
            "definitions": len(self.project.level_definitions),
            "groups": len(self.project.level_groups),
            "visible": len([item for item in self.project.levels if item.visible]),
            "locked": len([item for item in self.project.levels if item.locked]),
        }


@dataclass
class GridMetadata:
    """Professional BIM grid metadata."""

    description: str = ""
    prefix: str = ""
    classification: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe grid metadata."""

        return {
            "description": self.description,
            "prefix": self.prefix,
            "classification": dict(self.classification),
        }

    @staticmethod
    def from_dict(data):
        """Create grid metadata from persisted data."""

        data = data or {}

        return GridMetadata(
            data.get("description", ""),
            data.get("prefix", ""),
            dict(data.get("classification", {})),
        )


class GridLine(BIMMarker):
    """Professional BIM grid line referencing grid geometry."""

    type_name = "GridLine"

    def __init__(self, name="Grid Line", start=None, end=None, grid_id="", metadata=None):

        super().__init__(name)
        self.start = start or Vector3()
        self.end = end or Vector3(100.0, 0.0, 0.0)
        self.grid_id = grid_id
        self.metadata = (
            metadata
            if isinstance(metadata, GridMetadata)
            else GridMetadata.from_dict(metadata or {})
        )
        self.display_color = "#64b5f6"

    @property
    def location(self):
        """Return midpoint location."""

        return Vector3(
            (self.start.x + self.end.x) * 0.5,
            (self.start.y + self.end.y) * 0.5,
            (self.start.z + self.end.z) * 0.5,
        )

    @property
    def bounding_box3d(self):
        """Return grid line bounds."""

        box = BoundingBox3D()
        box.add(self.start)
        box.add(self.end)
        return box

    def points(self):
        """Return grid line points."""

        return [self.start, self.end]

    def segments(self):
        """Return grid line segment."""

        return [(self.start, self.end)]

    def to_dict(self):
        """Return JSON-safe grid line data."""

        return _marker_data(self, {
            "start": _vector_to_data(self.start),
            "end": _vector_to_data(self.end),
            "grid_id": self.grid_id,
            "metadata": self.metadata.to_dict(),
            "display_color": self.display_color,
        })

    @staticmethod
    def from_dict(data):
        """Create grid line from persisted data."""

        data = data or {}
        line = GridLine(
            data.get("name", "Grid Line"),
            _vector_from_data(data.get("start")),
            _vector_from_data(data.get("end")),
            data.get("grid_id", ""),
            GridMetadata.from_dict(data.get("metadata", {})),
        )
        _restore_marker(line, data)
        line.display_color = data.get("display_color", line.display_color)

        return line


class GridIntersection(BIMMarker):
    """Professional BIM grid intersection marker."""

    type_name = "GridIntersection"

    def __init__(self, name="Grid Intersection", point=None, grid_line_ids=None):

        super().__init__(name)
        self.point = point or Vector3()
        self.grid_line_ids = list(grid_line_ids or [])
        self.display_color = "#4fc3f7"

    @property
    def location(self):
        """Return intersection location."""

        return self.point

    @property
    def bounding_box3d(self):
        """Return compact intersection bounds."""

        box = BoundingBox3D()
        pad = 2.0
        box.add(self.point - Vector3(pad, pad, pad))
        box.add(self.point + Vector3(pad, pad, pad))
        return box

    def points(self):
        """Return intersection point."""

        return [self.point]

    def segments(self):
        """Return compact cross marker."""

        pad = 3.0

        return [
            (self.point - Vector3(pad, 0.0, 0.0), self.point + Vector3(pad, 0.0, 0.0)),
            (self.point - Vector3(0.0, pad, 0.0), self.point + Vector3(0.0, pad, 0.0)),
        ]

    def to_dict(self):
        """Return JSON-safe intersection data."""

        return _marker_data(self, {
            "point": _vector_to_data(self.point),
            "grid_line_ids": list(self.grid_line_ids),
            "display_color": self.display_color,
        })

    @staticmethod
    def from_dict(data):
        """Create grid intersection from persisted data."""

        data = data or {}
        intersection = GridIntersection(
            data.get("name", "Grid Intersection"),
            _vector_from_data(data.get("point")),
            data.get("grid_line_ids", []),
        )
        _restore_marker(intersection, data)
        intersection.display_color = data.get("display_color", intersection.display_color)

        return intersection


@dataclass
class GridGroup:
    """Named grouping of BIM grid lines."""

    name: str = "Grid Group"
    grid_line_ids: list = field(default_factory=list)
    visible: bool = True
    locked: bool = False
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe grid group data."""

        return {
            "id": self.id,
            "name": self.name,
            "grid_line_ids": list(self.grid_line_ids),
            "visible": self.visible,
            "locked": self.locked,
        }

    @staticmethod
    def from_dict(data):
        """Create grid group from persisted data."""

        data = data or {}

        return GridGroup(
            data.get("name", "Grid Group"),
            list(data.get("grid_line_ids", [])),
            bool(data.get("visible", True)),
            bool(data.get("locked", False)),
            data.get("id", str(uuid4())),
        )


@dataclass
class GridStatistics:
    """Professional grid statistics."""

    grid_lines: int = 0
    intersections: int = 0
    groups: int = 0

    def to_dict(self):
        """Return JSON-safe grid statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create grid statistics from persisted data."""

        data = data or {}

        return GridStatistics(
            int(data.get("grid_lines", 0)),
            int(data.get("intersections", 0)),
            int(data.get("groups", 0)),
        )


class GridManager:
    """Project-scoped professional BIM grid helper."""

    def __init__(self, project=None):

        self.project = project

    def add_line(self, line):
        """Store a grid line."""

        if line not in self.project.grid_lines:
            self.project.grid_lines.append(line)

        return line

    def add_intersection(self, intersection):
        """Store a grid intersection."""

        if intersection not in self.project.grid_intersections:
            self.project.grid_intersections.append(intersection)

        return intersection

    def add_group(self, group):
        """Store a grid group."""

        if group not in self.project.grid_groups:
            self.project.grid_groups.append(group)

        return group

    def statistics(self):
        """Return grid statistics."""

        stats = GridStatistics(
            len(self.project.grid_lines),
            len(self.project.grid_intersections),
            len(self.project.grid_groups),
        )
        self.project.grid_statistics = stats

        return stats


@dataclass
class ViewMetadata:
    """Professional BIM view metadata."""

    description: str = ""
    discipline: str = "Architecture"
    scale: str = "1:100"
    classification: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe view metadata."""

        return {
            "description": self.description,
            "discipline": self.discipline,
            "scale": self.scale,
            "classification": dict(self.classification),
        }

    @staticmethod
    def from_dict(data):
        """Create view metadata from persisted data."""

        data = data or {}

        return ViewMetadata(
            data.get("description", ""),
            data.get("discipline", "Architecture"),
            data.get("scale", "1:100"),
            dict(data.get("classification", {})),
        )


@dataclass
class ViewStatistics:
    """BIM view summary statistics."""

    views: int = 0
    templates: int = 0
    placed: int = 0

    def to_dict(self):
        """Return JSON-safe view statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create view statistics from persisted data."""

        data = data or {}

        return ViewStatistics(
            int(data.get("views", 0)),
            int(data.get("templates", 0)),
            int(data.get("placed", 0)),
        )


@dataclass
class ViewTemplate:
    """Reusable BIM view template."""

    name: str = "View Template"
    view_type: str = "FloorPlan"
    settings: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe template data."""

        return {
            "id": self.id,
            "name": self.name,
            "view_type": self.view_type,
            "settings": dict(self.settings),
        }

    @staticmethod
    def from_dict(data):
        """Create view template from persisted data."""

        data = data or {}

        return ViewTemplate(
            data.get("name", "View Template"),
            data.get("view_type", "FloorPlan"),
            dict(data.get("settings", {})),
            data.get("id", str(uuid4())),
        )


class BIMView(BIMMarker):
    """Base selectable BIM view marker referencing existing BIM data."""

    type_name = "BIMView"
    view_type = "3D View"

    def __init__(self, name="BIM View", level_id="", template_id="", metadata=None, location=None):

        super().__init__(name)
        self.level_id = level_id
        self.template_id = template_id
        self.metadata = (
            metadata
            if isinstance(metadata, ViewMetadata)
            else ViewMetadata.from_dict(metadata or {})
        )
        self.location = location or Vector3()
        self.scale = "1:100"
        self.viewed_entity_ids = []
        self.display_color = "#ffd54f"

    @property
    def bounding_box3d(self):
        """Return compact view marker bounds."""

        box = BoundingBox3D()
        pad = 8.0
        box.add(self.location - Vector3(pad, pad, pad))
        box.add(self.location + Vector3(pad, pad, pad))
        return box

    def points(self):
        """Return view marker point."""

        return [self.location]

    def segments(self):
        """Return view marker rectangle."""

        pad = 8.0
        a = self.location + Vector3(-pad, -pad, 0.0)
        b = self.location + Vector3(pad, -pad, 0.0)
        c = self.location + Vector3(pad, pad, 0.0)
        d = self.location + Vector3(-pad, pad, 0.0)

        return [(a, b), (b, c), (c, d), (d, a)]

    def to_dict(self):
        """Return JSON-safe view data."""

        return _marker_data(self, {
            "view_type": self.view_type,
            "level_id": self.level_id,
            "template_id": self.template_id,
            "metadata": self.metadata.to_dict(),
            "location": _vector_to_data(self.location),
            "scale": self.scale,
            "viewed_entity_ids": list(self.viewed_entity_ids),
            "display_color": self.display_color,
        })

    @classmethod
    def from_dict(cls, data):
        """Create view data from persistence."""

        data = data or {}
        view_class = _view_class_for(data.get("view_type", "3D View"))
        view = view_class(
            data.get("name", data.get("view_type", "BIM View")),
            data.get("level_id", ""),
            data.get("template_id", ""),
            ViewMetadata.from_dict(data.get("metadata", {})),
            _vector_from_data(data.get("location")),
        )
        _restore_marker(view, data)
        view.scale = data.get("scale", "1:100")
        view.viewed_entity_ids = list(data.get("viewed_entity_ids", []))
        view.display_color = data.get("display_color", view.display_color)

        return view


class FloorPlanView(BIMView):
    """BIM floor plan view."""

    type_name = "FloorPlanView"
    view_type = "FloorPlan"


class CeilingPlanView(BIMView):
    """BIM ceiling plan view."""

    type_name = "CeilingPlanView"
    view_type = "CeilingPlan"


class ElevationView(BIMView):
    """BIM elevation view."""

    type_name = "ElevationView"
    view_type = "Elevation"


class SectionView(BIMView):
    """BIM section view."""

    type_name = "SectionView"
    view_type = "Section"


class DetailView(BIMView):
    """BIM detail view."""

    type_name = "DetailView"
    view_type = "Detail"


class View3D(BIMView):
    """BIM 3D documentation view."""

    type_name = "View3D"
    view_type = "3D View"


class ViewManager:
    """Project-scoped BIM view helper."""

    def __init__(self, project=None):

        self.project = project

    def add_view(self, view):
        """Store a BIM view."""

        if view not in self.project.views:
            self.project.views.append(view)

        return view

    def add_template(self, template):
        """Store a view template."""

        if template not in self.project.view_templates:
            self.project.view_templates.append(template)

        return template

    def statistics(self):
        """Return view statistics."""

        stats = ViewStatistics(
            len(self.project.views),
            len(self.project.view_templates),
            len([sheet for sheet in self.project.sheets if sheet.viewport_references]),
        )
        self.project.view_statistics = stats

        return stats


@dataclass
class DrawingScale:
    """Drawing scale metadata."""

    name: str = "1:100"
    ratio: float = 100.0

    def to_dict(self):
        """Return JSON-safe drawing scale data."""

        return {"name": self.name, "ratio": self.ratio}

    @staticmethod
    def from_dict(data):
        """Create drawing scale data."""

        data = data or {}

        return DrawingScale(data.get("name", "1:100"), float(data.get("ratio", 100.0)))


@dataclass
class ViewPlacement:
    """Placement of a view on a drawing sheet."""

    x: float = 0.0
    y: float = 0.0
    width: float = 100.0
    height: float = 80.0

    def to_dict(self):
        """Return JSON-safe placement data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create view placement data."""

        data = data or {}

        return ViewPlacement(
            float(data.get("x", 0.0)),
            float(data.get("y", 0.0)),
            float(data.get("width", 100.0)),
            float(data.get("height", 80.0)),
        )


@dataclass
class ViewportReference:
    """Reference to an existing BIM view placed on a sheet."""

    view_id: str = ""
    placement: ViewPlacement = field(default_factory=ViewPlacement)
    scale: DrawingScale = field(default_factory=DrawingScale)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe viewport reference data."""

        return {
            "id": self.id,
            "view_id": self.view_id,
            "placement": self.placement.to_dict(),
            "scale": self.scale.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create viewport reference from persisted data."""

        data = data or {}

        return ViewportReference(
            data.get("view_id", ""),
            ViewPlacement.from_dict(data.get("placement", {})),
            DrawingScale.from_dict(data.get("scale", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class DocumentationSettings:
    """Persistent documentation defaults."""

    default_sheet_size: str = "A1"
    default_scale: str = "1:100"
    title_block: str = "Default Title Block"
    schedule_ready: bool = True
    legend_ready: bool = True

    def to_dict(self):
        """Return JSON-safe settings."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create documentation settings from persisted data."""

        data = data or {}

        return DocumentationSettings(
            data.get("default_sheet_size", "A1"),
            data.get("default_scale", "1:100"),
            data.get("title_block", "Default Title Block"),
            bool(data.get("schedule_ready", True)),
            bool(data.get("legend_ready", True)),
        )


class DrawingSheet(BIMMarker):
    """BIM drawing sheet referencing existing BIM views."""

    type_name = "DrawingSheet"

    def __init__(self, name="Drawing Sheet", number="A-001", title_block="Default Title Block", location=None):

        super().__init__(name)
        self.number = number
        self.title_block = title_block
        self.viewport_references = []
        self.location = location or Vector3()
        self.display_color = "#ffcc80"

    @property
    def bounding_box3d(self):
        """Return compact sheet marker bounds."""

        box = BoundingBox3D()
        pad = 10.0
        box.add(self.location - Vector3(pad, pad, pad))
        box.add(self.location + Vector3(pad, pad, pad))
        return box

    def add_viewport(self, viewport):
        """Add a view placement reference."""

        if viewport not in self.viewport_references:
            self.viewport_references.append(viewport)

        return viewport

    def points(self):
        """Return sheet marker point."""

        return [self.location]

    def segments(self):
        """Return sheet marker rectangle."""

        width = 14.0
        height = 10.0
        a = self.location + Vector3(-width, -height, 0.0)
        b = self.location + Vector3(width, -height, 0.0)
        c = self.location + Vector3(width, height, 0.0)
        d = self.location + Vector3(-width, height, 0.0)

        return [(a, b), (b, c), (c, d), (d, a), (a, c)]

    def to_dict(self):
        """Return JSON-safe drawing sheet data."""

        return _marker_data(self, {
            "number": self.number,
            "title_block": self.title_block,
            "viewport_references": [viewport.to_dict() for viewport in self.viewport_references],
            "location": _vector_to_data(self.location),
            "display_color": self.display_color,
        })

    @staticmethod
    def from_dict(data):
        """Create drawing sheet from persisted data."""

        data = data or {}
        sheet = DrawingSheet(
            data.get("name", "Drawing Sheet"),
            data.get("number", "A-001"),
            data.get("title_block", "Default Title Block"),
            _vector_from_data(data.get("location")),
        )
        _restore_marker(sheet, data)
        sheet.viewport_references = [
            ViewportReference.from_dict(item)
            for item in data.get("viewport_references", [])
        ]
        sheet.display_color = data.get("display_color", sheet.display_color)

        return sheet


class SheetManager:
    """Project-scoped BIM sheet helper."""

    def __init__(self, project=None):

        self.project = project

    def add_sheet(self, sheet):
        """Store a drawing sheet."""

        if sheet not in self.project.sheets:
            self.project.sheets.append(sheet)

        return sheet

    def statistics(self):
        """Return sheet statistics."""

        return {
            "sheets": len(self.project.sheets),
            "viewports": sum(len(sheet.viewport_references) for sheet in self.project.sheets),
        }


@dataclass
class ScheduleMetadata:
    """Professional BIM schedule metadata."""

    description: str = ""
    discipline: str = "Architecture"
    schedule_type: str = "Custom"
    classification: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe schedule metadata."""

        return {
            "description": self.description,
            "discipline": self.discipline,
            "schedule_type": self.schedule_type,
            "classification": dict(self.classification),
        }

    @staticmethod
    def from_dict(data):
        """Create schedule metadata from persisted data."""

        data = data or {}

        return ScheduleMetadata(
            data.get("description", ""),
            data.get("discipline", "Architecture"),
            data.get("schedule_type", "Custom"),
            dict(data.get("classification", {})),
        )


@dataclass
class ScheduleField:
    """Reusable schedule field definition."""

    name: str = "Name"
    source: str = "name"
    data_type: str = "text"
    heading: str = ""
    visible: bool = True
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe field data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create a schedule field from persisted data."""

        data = data or {}

        return ScheduleField(
            data.get("name", "Name"),
            data.get("source", "name"),
            data.get("data_type", "text"),
            data.get("heading", ""),
            bool(data.get("visible", True)),
            data.get("id", str(uuid4())),
        )


@dataclass
class ScheduleFilter:
    """Schedule row filter."""

    field: str = "name"
    operator: str = "contains"
    value: object = ""
    id: str = dataclasses.field(default_factory=lambda: str(uuid4()))

    def matches(self, row):
        """Return whether a schedule row passes this filter."""

        actual = row.values.get(self.field)

        if self.operator == "equals":
            return actual == self.value
        if self.operator == "not_equals":
            return actual != self.value
        if self.operator == "contains":
            return str(self.value).lower() in str(actual).lower()
        if self.operator == "exists":
            return actual not in (None, "")

        return True

    def to_dict(self):
        """Return JSON-safe filter data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create a filter from persisted data."""

        data = data or {}

        return ScheduleFilter(
            data.get("field", "name"),
            data.get("operator", "contains"),
            data.get("value", ""),
            data.get("id", str(uuid4())),
        )


@dataclass
class ScheduleSort:
    """Schedule sort rule."""

    field: str = "name"
    ascending: bool = True
    id: str = dataclasses.field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe sort data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create a sort rule from persisted data."""

        data = data or {}

        return ScheduleSort(
            data.get("field", "name"),
            bool(data.get("ascending", True)),
            data.get("id", str(uuid4())),
        )


@dataclass
class ScheduleGroup:
    """Schedule grouping rule."""

    field: str = "category"
    heading: str = ""
    id: str = dataclasses.field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe group data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create a group rule from persisted data."""

        data = data or {}

        return ScheduleGroup(
            data.get("field", "category"),
            data.get("heading", ""),
            data.get("id", str(uuid4())),
        )


@dataclass
class ScheduleColumn:
    """Schedule column display definition."""

    field: str = "name"
    heading: str = ""
    width: float = 120.0
    id: str = dataclasses.field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe column data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create a schedule column from persisted data."""

        data = data or {}

        return ScheduleColumn(
            data.get("field", "name"),
            data.get("heading", ""),
            float(data.get("width", 120.0)),
            data.get("id", str(uuid4())),
        )


@dataclass
class ScheduleRow:
    """Computed schedule row referencing existing BIM data."""

    source_id: str = ""
    values: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe row data."""

        return {
            "id": self.id,
            "source_id": self.source_id,
            "values": dict(self.values),
        }

    @staticmethod
    def from_dict(data):
        """Create a schedule row from persisted data."""

        data = data or {}

        return ScheduleRow(
            data.get("source_id", ""),
            dict(data.get("values", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class ScheduleStatistics:
    """BIM schedule summary statistics."""

    schedules: int = 0
    templates: int = 0
    rows: int = 0
    fields: int = 0

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create schedule statistics from persisted data."""

        data = data or {}

        return ScheduleStatistics(
            int(data.get("schedules", 0)),
            int(data.get("templates", 0)),
            int(data.get("rows", 0)),
            int(data.get("fields", 0)),
        )


class ScheduleDefinition:
    """Professional BIM schedule definition and computed rows."""

    def __init__(self, name="Schedule", schedule_type="Custom", metadata=None, template=False):

        self.id = str(uuid4())
        self.name = name
        self.schedule_type = schedule_type
        self.metadata = (
            metadata
            if isinstance(metadata, ScheduleMetadata)
            else ScheduleMetadata.from_dict(metadata or {"schedule_type": schedule_type})
        )
        self.fields = []
        self.filters = []
        self.sorts = []
        self.groups = []
        self.columns = []
        self.rows = []
        self.template = bool(template)
        self.visible = True
        self.locked = False

    def add_field(self, field_item):
        """Add a field and matching column if needed."""

        if field_item not in self.fields:
            self.fields.append(field_item)

        if not any(column.field == field_item.name for column in self.columns):
            self.columns.append(ScheduleColumn(field_item.name, field_item.heading or field_item.name))

        return field_item

    def to_dict(self):
        """Return JSON-safe schedule definition data."""

        return {
            "id": self.id,
            "name": self.name,
            "schedule_type": self.schedule_type,
            "metadata": self.metadata.to_dict(),
            "fields": [item.to_dict() for item in self.fields],
            "filters": [item.to_dict() for item in self.filters],
            "sorts": [item.to_dict() for item in self.sorts],
            "groups": [item.to_dict() for item in self.groups],
            "columns": [item.to_dict() for item in self.columns],
            "rows": [item.to_dict() for item in self.rows],
            "template": self.template,
            "visible": self.visible,
            "locked": self.locked,
        }

    @staticmethod
    def from_dict(data):
        """Create a schedule definition from persisted data."""

        data = data or {}
        schedule = ScheduleDefinition(
            data.get("name", "Schedule"),
            data.get("schedule_type", "Custom"),
            ScheduleMetadata.from_dict(data.get("metadata", {})),
            bool(data.get("template", False)),
        )
        schedule.id = data.get("id", schedule.id)
        schedule.fields = [ScheduleField.from_dict(item) for item in data.get("fields", [])]
        schedule.filters = [ScheduleFilter.from_dict(item) for item in data.get("filters", [])]
        schedule.sorts = [ScheduleSort.from_dict(item) for item in data.get("sorts", [])]
        schedule.groups = [ScheduleGroup.from_dict(item) for item in data.get("groups", [])]
        schedule.columns = [ScheduleColumn.from_dict(item) for item in data.get("columns", [])]
        schedule.rows = [ScheduleRow.from_dict(item) for item in data.get("rows", [])]
        schedule.visible = bool(data.get("visible", True))
        schedule.locked = bool(data.get("locked", False))

        return schedule


class ScheduleManager:
    """Project-scoped BIM schedule helper."""

    def __init__(self, project=None):

        self.project = project

    def add_schedule(self, schedule):
        """Store a schedule definition."""

        collection = self.project.schedule_templates if schedule.template else self.project.schedules

        if schedule not in collection:
            collection.append(schedule)

        self.statistics()

        return schedule

    def build_schedule(self, schedule):
        """Build schedule rows from existing BIM project data."""

        schedule.rows = [
            ScheduleRow(getattr(item, "id", ""), _schedule_values(item, schedule.fields, self.project))
            for item in _schedule_sources(schedule, self.project)
        ]
        schedule.rows = [row for row in schedule.rows if all(filter_item.matches(row) for filter_item in schedule.filters)]

        for sort_rule in reversed(schedule.sorts):
            schedule.rows.sort(
                key=lambda row: str(row.values.get(sort_rule.field, "")),
                reverse=not sort_rule.ascending,
            )

        self.statistics()

        return schedule.rows

    def schedules_for(self, item):
        """Return schedules containing rows for an item."""

        item_id = getattr(item, "id", item)

        return [
            schedule for schedule in self.project.schedules
            if any(row.source_id == item_id for row in schedule.rows)
        ]

    def statistics(self):
        """Return schedule statistics."""

        stats = ScheduleStatistics(
            len(self.project.schedules),
            len(self.project.schedule_templates),
            sum(len(schedule.rows) for schedule in self.project.schedules),
            sum(len(schedule.fields) for schedule in self.project.schedules),
        )
        self.project.schedule_statistics = stats

        return stats


@dataclass
class ClassificationMetadata:
    """Classification system metadata."""

    description: str = ""
    source: str = ""
    version: str = ""
    placeholders: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe metadata."""

        return {
            "description": self.description,
            "source": self.source,
            "version": self.version,
            "placeholders": dict(self.placeholders),
        }

    @staticmethod
    def from_dict(data):
        """Create classification metadata from persistence."""

        data = data or {}

        return ClassificationMetadata(
            data.get("description", ""),
            data.get("source", ""),
            data.get("version", ""),
            dict(data.get("placeholders", {})),
        )


@dataclass
class ClassificationCode:
    """Classification code entry."""

    code: str = ""
    title: str = ""
    description: str = ""
    parent_code: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe code data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create a classification code."""

        data = data or {}

        return ClassificationCode(
            data.get("code", ""),
            data.get("title", ""),
            data.get("description", ""),
            data.get("parent_code", ""),
            data.get("id", str(uuid4())),
        )


class ClassificationSystem:
    """Reusable BIM classification system."""

    def __init__(self, name="Custom Classification", metadata=None):

        self.id = str(uuid4())
        self.name = name
        self.metadata = (
            metadata
            if isinstance(metadata, ClassificationMetadata)
            else ClassificationMetadata.from_dict(metadata or {})
        )
        self.codes = []

    def add_code(self, code):
        """Store a classification code."""

        if code not in self.codes:
            self.codes.append(code)

        return code

    def to_dict(self):
        """Return JSON-safe classification system data."""

        return {
            "id": self.id,
            "name": self.name,
            "metadata": self.metadata.to_dict(),
            "codes": [code.to_dict() for code in self.codes],
        }

    @staticmethod
    def from_dict(data):
        """Create a classification system from persisted data."""

        data = data or {}
        system = ClassificationSystem(
            data.get("name", "Custom Classification"),
            ClassificationMetadata.from_dict(data.get("metadata", {})),
        )
        system.id = data.get("id", system.id)
        system.codes = [ClassificationCode.from_dict(item) for item in data.get("codes", [])]

        return system


@dataclass
class ClassificationMapping:
    """Relationship between an existing BIM item and a classification code."""

    target_id: str = ""
    system_id: str = ""
    code: str = ""
    code_id: str = ""
    metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe mapping data."""

        return {
            "id": self.id,
            "target_id": self.target_id,
            "system_id": self.system_id,
            "code": self.code,
            "code_id": self.code_id,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a classification mapping from persistence."""

        data = data or {}

        return ClassificationMapping(
            data.get("target_id", ""),
            data.get("system_id", ""),
            data.get("code", ""),
            data.get("code_id", ""),
            dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class ClassificationStatistics:
    """Classification summary statistics."""

    systems: int = 0
    codes: int = 0
    mappings: int = 0

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create classification statistics."""

        data = data or {}

        return ClassificationStatistics(
            int(data.get("systems", 0)),
            int(data.get("codes", 0)),
            int(data.get("mappings", 0)),
        )


class ClassificationManager:
    """Project-scoped classification helper."""

    def __init__(self, project=None):

        self.project = project

    def add_system(self, system):
        """Store a classification system."""

        if system not in self.project.classification_systems:
            self.project.classification_systems.append(system)

        self.statistics()

        return system

    def add_mapping(self, mapping):
        """Store a classification mapping."""

        if mapping not in self.project.classification_mappings:
            self.project.classification_mappings.append(mapping)

        target = _find_by_id(
            self.project.instances +
            self.project.types +
            self.project.element_definitions +
            self.project.families,
            mapping.target_id,
        )

        if target is not None and hasattr(target, "classification"):
            target.classification[mapping.system_id or "Classification"] = mapping.code

        self.statistics()

        return mapping

    def mappings_for(self, item):
        """Return all classifications assigned to an item."""

        item_id = getattr(item, "id", item)

        return [
            mapping for mapping in self.project.classification_mappings
            if mapping.target_id == item_id
        ]

    def statistics(self):
        """Return classification statistics."""

        stats = ClassificationStatistics(
            len(self.project.classification_systems),
            sum(len(system.codes) for system in self.project.classification_systems),
            len(self.project.classification_mappings),
        )
        self.project.classification_statistics = stats

        return stats


@dataclass
class IFCMetadata:
    """IFC foundation metadata."""

    schema: str = "IFC4"
    author: str = ""
    application: str = "Kinematics Studio"
    description: str = ""
    placeholders: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe IFC metadata."""

        return {
            "schema": self.schema,
            "author": self.author,
            "application": self.application,
            "description": self.description,
            "placeholders": dict(self.placeholders),
        }

    @staticmethod
    def from_dict(data):
        """Create IFC metadata."""

        data = data or {}

        return IFCMetadata(
            data.get("schema", "IFC4"),
            data.get("author", ""),
            data.get("application", "Kinematics Studio"),
            data.get("description", ""),
            dict(data.get("placeholders", {})),
        )


@dataclass
class IFCProject:
    """IFC project metadata referencing the active BIM project."""

    name: str = "IFC Project"
    bim_project_id: str = ""
    metadata: IFCMetadata = field(default_factory=IFCMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe IFC project data."""

        return {
            "id": self.id,
            "name": self.name,
            "bim_project_id": self.bim_project_id,
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create IFC project data."""

        data = data or {}

        return IFCProject(
            data.get("name", "IFC Project"),
            data.get("bim_project_id", ""),
            IFCMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class IFCSite:
    """IFC site metadata referencing an existing BIM site."""

    name: str = "IFC Site"
    bim_site_id: str = ""
    metadata: IFCMetadata = field(default_factory=IFCMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe IFC site data."""

        return {
            "id": self.id,
            "name": self.name,
            "bim_site_id": self.bim_site_id,
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create IFC site data."""

        data = data or {}

        return IFCSite(data.get("name", "IFC Site"), data.get("bim_site_id", ""), IFCMetadata.from_dict(data.get("metadata", {})), data.get("id", str(uuid4())))


@dataclass
class IFCBuilding:
    """IFC building metadata referencing an existing BIM building."""

    name: str = "IFC Building"
    bim_building_id: str = ""
    ifc_site_id: str = ""
    metadata: IFCMetadata = field(default_factory=IFCMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe IFC building data."""

        return dict(self.__dict__, metadata=self.metadata.to_dict())

    @staticmethod
    def from_dict(data):
        """Create IFC building data."""

        data = data or {}

        return IFCBuilding(data.get("name", "IFC Building"), data.get("bim_building_id", ""), data.get("ifc_site_id", ""), IFCMetadata.from_dict(data.get("metadata", {})), data.get("id", str(uuid4())))


@dataclass
class IFCStorey:
    """IFC storey metadata referencing an existing BIM level."""

    name: str = "IFC Storey"
    bim_level_id: str = ""
    ifc_building_id: str = ""
    elevation: float = 0.0
    metadata: IFCMetadata = field(default_factory=IFCMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe IFC storey data."""

        return dict(self.__dict__, metadata=self.metadata.to_dict())

    @staticmethod
    def from_dict(data):
        """Create IFC storey data."""

        data = data or {}

        return IFCStorey(data.get("name", "IFC Storey"), data.get("bim_level_id", ""), data.get("ifc_building_id", ""), float(data.get("elevation", 0.0)), IFCMetadata.from_dict(data.get("metadata", {})), data.get("id", str(uuid4())))


@dataclass
class IFCElement:
    """IFC element metadata referencing existing BIM instance and MeshEntity geometry."""

    name: str = "IFC Element"
    bim_instance_id: str = ""
    mesh_entity_id: str = ""
    ifc_type: str = "IfcBuildingElementProxy"
    ifc_storey_id: str = ""
    metadata: IFCMetadata = field(default_factory=IFCMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe IFC element data."""

        return dict(self.__dict__, metadata=self.metadata.to_dict())

    @staticmethod
    def from_dict(data):
        """Create IFC element metadata."""

        data = data or {}

        return IFCElement(
            data.get("name", "IFC Element"),
            data.get("bim_instance_id", ""),
            data.get("mesh_entity_id", ""),
            data.get("ifc_type", "IfcBuildingElementProxy"),
            data.get("ifc_storey_id", ""),
            IFCMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class IFCRelationship:
    """IFC relationship metadata between existing BIM/IFC references."""

    name: str = "IFC Relationship"
    relationship_type: str = "IfcRelAssociates"
    source_id: str = ""
    target_ids: list = field(default_factory=list)
    metadata: IFCMetadata = field(default_factory=IFCMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe IFC relationship data."""

        return {
            "id": self.id,
            "name": self.name,
            "relationship_type": self.relationship_type,
            "source_id": self.source_id,
            "target_ids": list(self.target_ids),
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create IFC relationship metadata."""

        data = data or {}

        return IFCRelationship(
            data.get("name", "IFC Relationship"),
            data.get("relationship_type", "IfcRelAssociates"),
            data.get("source_id", ""),
            list(data.get("target_ids", [])),
            IFCMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class IFCPropertySet:
    """IFC property-set metadata referencing existing BIM property sets."""

    name: str = "IFC Property Set"
    bim_property_set_id: str = ""
    target_id: str = ""
    properties: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe IFC property-set data."""

        return {
            "id": self.id,
            "name": self.name,
            "bim_property_set_id": self.bim_property_set_id,
            "target_id": self.target_id,
            "properties": dict(self.properties),
        }

    @staticmethod
    def from_dict(data):
        """Create IFC property-set metadata."""

        data = data or {}

        return IFCPropertySet(
            data.get("name", "IFC Property Set"),
            data.get("bim_property_set_id", ""),
            data.get("target_id", ""),
            dict(data.get("properties", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class IFCExportSettings:
    """Future IFC export settings placeholder."""

    schema: str = "IFC4"
    include_geometry: bool = False
    include_property_sets: bool = True
    options: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe export settings."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create IFC export settings."""

        data = data or {}

        return IFCExportSettings(data.get("schema", "IFC4"), bool(data.get("include_geometry", False)), bool(data.get("include_property_sets", True)), dict(data.get("options", {})))


@dataclass
class IFCImportSettings:
    """Future IFC import settings placeholder."""

    schema: str = "IFC4"
    link_existing_geometry: bool = True
    import_property_sets: bool = True
    options: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe import settings."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create IFC import settings."""

        data = data or {}

        return IFCImportSettings(data.get("schema", "IFC4"), bool(data.get("link_existing_geometry", True)), bool(data.get("import_property_sets", True)), dict(data.get("options", {})))


class IFCManager:
    """Project-scoped IFC metadata and relationship helper."""

    def __init__(self, project=None):

        self.project = project

    def add_item(self, item):
        """Store an IFC foundation item."""

        collection = self._collection_for(item)

        if collection is not None and item not in collection:
            collection.append(item)

        return item

    def status_for(self, item):
        """Return IFC mapping status for an existing BIM item."""

        item_id = getattr(item, "id", item)

        return "Linked" if any(element.bim_instance_id == item_id for element in self.project.ifc_elements) else "Unmapped"

    def element_for(self, item):
        """Return the IFC element linked to a BIM item."""

        item_id = getattr(item, "id", item)

        return next((element for element in self.project.ifc_elements if element.bim_instance_id == item_id), None)

    def statistics(self):
        """Return IFC foundation statistics."""

        return {
            "projects": 1 if self.project.ifc_project is not None else 0,
            "sites": len(self.project.ifc_sites),
            "buildings": len(self.project.ifc_buildings),
            "storeys": len(self.project.ifc_storeys),
            "elements": len(self.project.ifc_elements),
            "relationships": len(self.project.ifc_relationships),
            "property_sets": len(self.project.ifc_property_sets),
        }

    def _collection_for(self, item):
        if isinstance(item, IFCProject):
            self.project.ifc_project = item
            return None
        if isinstance(item, IFCSite):
            return self.project.ifc_sites
        if isinstance(item, IFCBuilding):
            return self.project.ifc_buildings
        if isinstance(item, IFCStorey):
            return self.project.ifc_storeys
        if isinstance(item, IFCElement):
            return self.project.ifc_elements
        if isinstance(item, IFCRelationship):
            return self.project.ifc_relationships
        if isinstance(item, IFCPropertySet):
            return self.project.ifc_property_sets

        return None


@dataclass
class RelationshipType:
    """BIM relationship type descriptor."""

    name: str = "Reference"
    inverse_name: str = "Referenced By"
    category: str = "Reference"
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe relationship type data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create a relationship type from persisted data."""

        data = data or {}

        return RelationshipType(
            data.get("name", "Reference"),
            data.get("inverse_name", "Referenced By"),
            data.get("category", "Reference"),
            data.get("id", str(uuid4())),
        )


@dataclass
class RelationshipMetadata:
    """Professional BIM relationship metadata."""

    description: str = ""
    discipline: str = "Architecture"
    validation_status: str = "Unchecked"
    properties: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe relationship metadata."""

        return {
            "description": self.description,
            "discipline": self.discipline,
            "validation_status": self.validation_status,
            "properties": dict(self.properties),
        }

    @staticmethod
    def from_dict(data):
        """Create relationship metadata from persisted data."""

        data = data or {}

        return RelationshipMetadata(
            data.get("description", ""),
            data.get("discipline", "Architecture"),
            data.get("validation_status", "Unchecked"),
            dict(data.get("properties", {})),
        )


@dataclass
class BIMRelationship:
    """Relationship edge between existing BIM objects."""

    source_id: str = ""
    target_id: str = ""
    relationship_type: str = "Reference"
    metadata: RelationshipMetadata = field(default_factory=RelationshipMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe relationship data."""

        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_type": self.relationship_type,
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create a relationship edge from persisted data."""

        data = data or {}

        return BIMRelationship(
            data.get("source_id", ""),
            data.get("target_id", ""),
            data.get("relationship_type", "Reference"),
            RelationshipMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class RelationshipStatistics:
    """BIM relationship graph statistics."""

    relationships: int = 0
    types: int = 0
    hosts: int = 0
    openings: int = 0
    connections: int = 0

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create relationship statistics from persisted data."""

        data = data or {}

        return RelationshipStatistics(
            int(data.get("relationships", 0)),
            int(data.get("types", 0)),
            int(data.get("hosts", 0)),
            int(data.get("openings", 0)),
            int(data.get("connections", 0)),
        )


class RelationshipManager:
    """Project-scoped BIM relationship graph helper."""

    DEFAULT_TYPES = (
        "Parent", "Child", "Host", "Hosted", "Contained", "Container",
        "Adjacent", "Connected", "Dependent", "Reference", "Aggregation", "Grouping",
    )

    def __init__(self, project=None):

        self.project = project

    def ensure_default_types(self):
        """Create default relationship type descriptors when missing."""

        existing = {item.name for item in self.project.relationship_types}

        for name in self.DEFAULT_TYPES:
            if name not in existing:
                self.project.relationship_types.append(
                    RelationshipType(name, _inverse_relationship_name(name), "BIM")
                )

        return self.project.relationship_types

    def add_type(self, relationship_type):
        """Store a relationship type."""

        if relationship_type not in self.project.relationship_types:
            self.project.relationship_types.append(relationship_type)

        self.statistics()

        return relationship_type

    def add_relationship(self, relationship):
        """Store a relationship edge between existing BIM objects."""

        if relationship not in self.project.relationships:
            self.project.relationships.append(relationship)

        source = _find_by_id(self.project.instances, relationship.source_id)
        if source is not None:
            bucket = relationship.relationship_type.lower()
            source.relationships.setdefault(bucket, [])
            if relationship.target_id not in source.relationships[bucket]:
                source.relationships[bucket].append(relationship.target_id)

        self.statistics()

        return relationship

    def relationships_for(self, item, relationship_type=None):
        """Return relationship edges connected to an item."""

        item_id = getattr(item, "id", item)

        return [
            relationship for relationship in self.project.relationships
            if item_id in (relationship.source_id, relationship.target_id)
            and (relationship_type is None or relationship.relationship_type == relationship_type)
        ]

    def related_items(self, item, relationship_type=None):
        """Return BIM instances related to an item."""

        item_id = getattr(item, "id", item)
        related_ids = []

        for relationship in self.relationships_for(item, relationship_type):
            related_ids.append(
                relationship.target_id
                if relationship.source_id == item_id else relationship.source_id
            )

        return [
            instance for instance in self.project.instances
            if instance.id in related_ids
        ]

    def validate_relationship(self, relationship):
        """Return whether both relationship endpoints exist."""

        return (
            self._has_reference(relationship.source_id) and
            self._has_reference(relationship.target_id)
        )

    def statistics(self):
        """Return relationship graph statistics."""

        stats = RelationshipStatistics(
            len(self.project.relationships),
            len(self.project.relationship_types),
            len(self.project.host_objects),
            len(self.project.openings),
            len(self.project.connections),
        )
        self.project.relationship_statistics = stats

        return stats

    def _has_reference(self, identifier):
        return _find_by_id(self.project.instances, identifier) is not None


@dataclass
class HostMetadata:
    """Host object metadata."""

    description: str = ""
    host_type: str = "Generic"
    validation_status: str = "Unchecked"
    properties: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe host metadata."""

        return {
            "description": self.description,
            "host_type": self.host_type,
            "validation_status": self.validation_status,
            "properties": dict(self.properties),
        }

    @staticmethod
    def from_dict(data):
        """Create host metadata from persistence."""

        data = data or {}

        return HostMetadata(
            data.get("description", ""),
            data.get("host_type", "Generic"),
            data.get("validation_status", "Unchecked"),
            dict(data.get("properties", {})),
        )


@dataclass
class OpeningMetadata:
    """Opening or void metadata."""

    description: str = ""
    opening_type: str = "Generic"
    validation_status: str = "Unchecked"
    properties: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe opening metadata."""

        return {
            "description": self.description,
            "opening_type": self.opening_type,
            "validation_status": self.validation_status,
            "properties": dict(self.properties),
        }

    @staticmethod
    def from_dict(data):
        """Create opening metadata from persistence."""

        data = data or {}

        return OpeningMetadata(
            data.get("description", ""),
            data.get("opening_type", "Generic"),
            data.get("validation_status", "Unchecked"),
            dict(data.get("properties", {})),
        )


@dataclass
class HostObject:
    """Host metadata referencing an existing BIM instance."""

    host_id: str = ""
    hosted_ids: list = field(default_factory=list)
    metadata: HostMetadata = field(default_factory=HostMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe host object data."""

        return {
            "id": self.id,
            "host_id": self.host_id,
            "hosted_ids": list(self.hosted_ids),
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create host object metadata."""

        data = data or {}

        return HostObject(
            data.get("host_id", ""),
            list(data.get("hosted_ids", [])),
            HostMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class HostedObject:
    """Hosted element metadata referencing existing BIM instances."""

    hosted_id: str = ""
    host_id: str = ""
    metadata: HostMetadata = field(default_factory=HostMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe hosted object data."""

        return {
            "id": self.id,
            "hosted_id": self.hosted_id,
            "host_id": self.host_id,
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create hosted object metadata."""

        data = data or {}

        return HostedObject(
            data.get("hosted_id", ""),
            data.get("host_id", ""),
            HostMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class Opening:
    """Opening metadata referencing existing BIM instances and hosts."""

    name: str = "Opening"
    host_id: str = ""
    opening_instance_id: str = ""
    hosted_id: str = ""
    metadata: OpeningMetadata = field(default_factory=OpeningMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe opening data."""

        return {
            "id": self.id,
            "name": self.name,
            "host_id": self.host_id,
            "opening_instance_id": self.opening_instance_id,
            "hosted_id": self.hosted_id,
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create opening metadata."""

        data = data or {}

        return Opening(
            data.get("name", "Opening"),
            data.get("host_id", ""),
            data.get("opening_instance_id", ""),
            data.get("hosted_id", ""),
            OpeningMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


class Void(Opening):
    """Void opening metadata."""

    @staticmethod
    def from_dict(data):
        """Create void metadata."""

        data = data or {}

        return Void(
            data.get("name", "Opening"),
            data.get("host_id", ""),
            data.get("opening_instance_id", ""),
            data.get("hosted_id", ""),
            OpeningMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class CutRelationship:
    """Relationship between a host and opening/void metadata."""

    host_id: str = ""
    opening_id: str = ""
    cutter_id: str = ""
    metadata: OpeningMetadata = field(default_factory=OpeningMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe cut relationship data."""

        return {
            "id": self.id,
            "host_id": self.host_id,
            "opening_id": self.opening_id,
            "cutter_id": self.cutter_id,
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create cut relationship metadata."""

        data = data or {}

        return CutRelationship(
            data.get("host_id", ""),
            data.get("opening_id", ""),
            data.get("cutter_id", ""),
            OpeningMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class ConnectionType:
    """Connectivity type descriptor."""

    name: str = "Generic"
    category: str = "Generic"
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe connection type data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create connection type metadata."""

        data = data or {}

        return ConnectionType(
            data.get("name", "Generic"),
            data.get("category", "Generic"),
            data.get("id", str(uuid4())),
        )


@dataclass
class ConnectionMetadata:
    """BIM connectivity metadata."""

    description: str = ""
    connection_status: str = "Unchecked"
    properties: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe connection metadata."""

        return {
            "description": self.description,
            "connection_status": self.connection_status,
            "properties": dict(self.properties),
        }

    @staticmethod
    def from_dict(data):
        """Create connection metadata from persistence."""

        data = data or {}

        return ConnectionMetadata(
            data.get("description", ""),
            data.get("connection_status", "Unchecked"),
            dict(data.get("properties", {})),
        )


@dataclass
class Connection:
    """Connectivity edge between existing BIM instances."""

    source_id: str = ""
    target_id: str = ""
    connection_type: str = "Generic"
    metadata: ConnectionMetadata = field(default_factory=ConnectionMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe connection data."""

        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "connection_type": self.connection_type,
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create connection metadata from persistence."""

        data = data or {}

        return Connection(
            data.get("source_id", ""),
            data.get("target_id", ""),
            data.get("connection_type", "Generic"),
            ConnectionMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class ConnectionStatistics:
    """Connectivity graph statistics."""

    connections: int = 0
    types: int = 0
    connected_elements: int = 0

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create connection statistics."""

        data = data or {}

        return ConnectionStatistics(
            int(data.get("connections", 0)),
            int(data.get("types", 0)),
            int(data.get("connected_elements", 0)),
        )


class ConnectivityManager:
    """Project-scoped BIM connectivity graph helper."""

    DEFAULT_TYPES = (
        "Wall", "Beam", "Column", "Foundation", "Generic",
    )

    def __init__(self, project=None):

        self.project = project

    def ensure_default_types(self):
        """Create default connection type descriptors when missing."""

        existing = {item.name for item in self.project.connection_types}

        for name in self.DEFAULT_TYPES:
            if name not in existing:
                self.project.connection_types.append(ConnectionType(name, name))

        return self.project.connection_types

    def add_type(self, connection_type):
        """Store a connection type."""

        if connection_type not in self.project.connection_types:
            self.project.connection_types.append(connection_type)

        self.statistics()

        return connection_type

    def add_connection(self, connection):
        """Store a connectivity edge."""

        if connection not in self.project.connections:
            self.project.connections.append(connection)

        self.statistics()

        return connection

    def connections_for(self, item):
        """Return connections touching an item."""

        item_id = getattr(item, "id", item)

        return [
            connection for connection in self.project.connections
            if item_id in (connection.source_id, connection.target_id)
        ]

    def connected_items(self, item):
        """Return BIM instances connected to an item."""

        item_id = getattr(item, "id", item)
        related_ids = []

        for connection in self.connections_for(item):
            related_ids.append(connection.target_id if connection.source_id == item_id else connection.source_id)

        return [
            instance for instance in self.project.instances
            if instance.id in related_ids
        ]

    def statistics(self):
        """Return connection statistics."""

        connected_ids = set()

        for connection in self.project.connections:
            connected_ids.add(connection.source_id)
            connected_ids.add(connection.target_id)

        stats = ConnectionStatistics(
            len(self.project.connections),
            len(self.project.connection_types),
            len(connected_ids),
        )
        self.project.connection_statistics = stats

        return stats


@dataclass
class OptionMetadata:
    """Design option metadata."""

    description: str = ""
    discipline: str = "Architecture"
    status: str = "Active"
    properties: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe option metadata."""

        return {
            "description": self.description,
            "discipline": self.discipline,
            "status": self.status,
            "properties": dict(self.properties),
        }

    @staticmethod
    def from_dict(data):
        """Create option metadata from persistence."""

        data = data or {}

        return OptionMetadata(
            data.get("description", ""),
            data.get("discipline", "Architecture"),
            data.get("status", "Active"),
            dict(data.get("properties", {})),
        )


@dataclass
class DesignOption:
    """Design option referencing existing BIM elements."""

    name: str = "Design Option"
    option_set_id: str = ""
    primary: bool = False
    active: bool = False
    metadata: OptionMetadata = field(default_factory=OptionMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe design option data."""

        return {
            "id": self.id,
            "name": self.name,
            "option_set_id": self.option_set_id,
            "primary": self.primary,
            "active": self.active,
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create a design option from persisted data."""

        data = data or {}

        return DesignOption(
            data.get("name", "Design Option"),
            data.get("option_set_id", ""),
            bool(data.get("primary", False)),
            bool(data.get("active", False)),
            OptionMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


class PrimaryOption(DesignOption):
    """Primary design option."""

    def __init__(self, name="Primary Option", option_set_id="", metadata=None, id=None):

        super().__init__(name, option_set_id, True, True, metadata or OptionMetadata(), id or str(uuid4()))


class SecondaryOption(DesignOption):
    """Secondary design option."""

    def __init__(self, name="Secondary Option", option_set_id="", metadata=None, id=None):

        super().__init__(name, option_set_id, False, False, metadata or OptionMetadata(), id or str(uuid4()))


@dataclass
class DesignOptionSet:
    """Container for related design options."""

    name: str = "Design Option Set"
    option_ids: list = field(default_factory=list)
    active_option_id: str = ""
    metadata: OptionMetadata = field(default_factory=OptionMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe design option set data."""

        return {
            "id": self.id,
            "name": self.name,
            "option_ids": list(self.option_ids),
            "active_option_id": self.active_option_id,
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create an option set from persistence."""

        data = data or {}

        return DesignOptionSet(
            data.get("name", "Design Option Set"),
            list(data.get("option_ids", [])),
            data.get("active_option_id", ""),
            OptionMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class OptionMembership:
    """Assignment of an existing BIM element to a design option."""

    element_id: str = ""
    option_id: str = ""
    option_set_id: str = ""
    metadata: OptionMetadata = field(default_factory=OptionMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe option membership data."""

        return {
            "id": self.id,
            "element_id": self.element_id,
            "option_id": self.option_id,
            "option_set_id": self.option_set_id,
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create option membership from persistence."""

        data = data or {}

        return OptionMembership(
            data.get("element_id", ""),
            data.get("option_id", ""),
            data.get("option_set_id", ""),
            OptionMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class OptionStatistics:
    """Design option statistics."""

    option_sets: int = 0
    options: int = 0
    memberships: int = 0
    active_options: int = 0

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create option statistics."""

        data = data or {}

        return OptionStatistics(
            int(data.get("option_sets", 0)),
            int(data.get("options", 0)),
            int(data.get("memberships", 0)),
            int(data.get("active_options", 0)),
        )


class DesignOptionManager:
    """Project-scoped design option helper."""

    def __init__(self, project=None):

        self.project = project

    def add_set(self, option_set):
        """Store a design option set."""

        if option_set not in self.project.design_option_sets:
            self.project.design_option_sets.append(option_set)

        self.statistics()

        return option_set

    def add_option(self, option):
        """Store a design option."""

        if option not in self.project.design_options:
            self.project.design_options.append(option)

        option_set = self.option_set_for(option.option_set_id)
        if option_set is not None and option.id not in option_set.option_ids:
            option_set.option_ids.append(option.id)
        if option.primary and option_set is not None and not option_set.active_option_id:
            option_set.active_option_id = option.id

        self.statistics()

        return option

    def add_membership(self, membership):
        """Assign an existing BIM element to an option."""

        if membership not in self.project.option_memberships:
            self.project.option_memberships.append(membership)

        self.statistics()

        return membership

    def activate(self, option):
        """Activate one option in its option set."""

        target = self.option_for(option)

        if target is None:
            return None

        for item in self.project.design_options:
            if item.option_set_id == target.option_set_id:
                item.active = item.id == target.id

        option_set = self.option_set_for(target.option_set_id)
        if option_set is not None:
            option_set.active_option_id = target.id

        self.statistics()

        return target

    def deactivate(self, option):
        """Deactivate a design option."""

        target = self.option_for(option)

        if target is not None:
            target.active = False

        self.statistics()

        return target

    def option_for(self, option):
        """Return a design option by object, id or name."""

        if isinstance(option, DesignOption):
            return option if option in self.project.design_options else None

        return _find_by_id(self.project.design_options, option)

    def option_set_for(self, option_set):
        """Return an option set by object, id or name."""

        if isinstance(option_set, DesignOptionSet):
            return option_set if option_set in self.project.design_option_sets else None

        return _find_by_id(self.project.design_option_sets, option_set)

    def memberships_for(self, item):
        """Return option memberships for an existing BIM element."""

        item_id = getattr(item, "id", item)

        return [
            membership for membership in self.project.option_memberships
            if membership.element_id == item_id
        ]

    def active_options(self):
        """Return active design options."""

        return [option for option in self.project.design_options if option.active]

    def statistics(self):
        """Return option statistics."""

        stats = OptionStatistics(
            len(self.project.design_option_sets),
            len(self.project.design_options),
            len(self.project.option_memberships),
            len(self.active_options()),
        )
        self.project.option_statistics = stats

        return stats


@dataclass
class PhaseMetadata:
    """Project phase metadata."""

    description: str = ""
    status: str = "Active"
    properties: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe phase metadata."""

        return {
            "description": self.description,
            "status": self.status,
            "properties": dict(self.properties),
        }

    @staticmethod
    def from_dict(data):
        """Create phase metadata from persistence."""

        data = data or {}

        return PhaseMetadata(
            data.get("description", ""),
            data.get("status", "Active"),
            dict(data.get("properties", {})),
        )


@dataclass
class ProjectPhase:
    """Project phase definition."""

    name: str = "New Construction"
    phase_type: str = "New Construction"
    sequence: int = 0
    visible: bool = True
    metadata: PhaseMetadata = field(default_factory=PhaseMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe phase data."""

        return {
            "id": self.id,
            "name": self.name,
            "phase_type": self.phase_type,
            "sequence": self.sequence,
            "visible": self.visible,
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create a project phase from persistence."""

        data = data or {}

        return ProjectPhase(
            data.get("name", "New Construction"),
            data.get("phase_type", "New Construction"),
            int(data.get("sequence", 0)),
            bool(data.get("visible", True)),
            PhaseMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class PhaseSequence:
    """Ordered phase sequence."""

    name: str = "Default Phase Sequence"
    phase_ids: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe phase sequence data."""

        return {"id": self.id, "name": self.name, "phase_ids": list(self.phase_ids)}

    @staticmethod
    def from_dict(data):
        """Create a phase sequence from persistence."""

        data = data or {}

        return PhaseSequence(data.get("name", "Default Phase Sequence"), list(data.get("phase_ids", [])), data.get("id", str(uuid4())))


@dataclass
class PhaseFilter:
    """Phase visibility filter."""

    name: str = "Show All"
    visible_phase_ids: list = field(default_factory=list)
    show_existing: bool = True
    show_demolition: bool = True
    show_new: bool = True
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe phase filter data."""

        return {
            "id": self.id,
            "name": self.name,
            "visible_phase_ids": list(self.visible_phase_ids),
            "show_existing": self.show_existing,
            "show_demolition": self.show_demolition,
            "show_new": self.show_new,
        }

    @staticmethod
    def from_dict(data):
        """Create a phase filter from persistence."""

        data = data or {}

        return PhaseFilter(
            data.get("name", "Show All"),
            list(data.get("visible_phase_ids", [])),
            bool(data.get("show_existing", True)),
            bool(data.get("show_demolition", True)),
            bool(data.get("show_new", True)),
            data.get("id", str(uuid4())),
        )


@dataclass
class PhaseAssignment:
    """Assignment of an existing BIM element to project phases."""

    element_id: str = ""
    created_phase_id: str = ""
    demolished_phase_id: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe phase assignment data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create phase assignment from persistence."""

        data = data or {}

        return PhaseAssignment(
            data.get("element_id", ""),
            data.get("created_phase_id", ""),
            data.get("demolished_phase_id", ""),
            data.get("id", str(uuid4())),
        )


@dataclass
class PhaseStatistics:
    """Phase summary statistics."""

    phases: int = 0
    sequences: int = 0
    filters: int = 0
    assignments: int = 0

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create phase statistics."""

        data = data or {}

        return PhaseStatistics(
            int(data.get("phases", 0)),
            int(data.get("sequences", 0)),
            int(data.get("filters", 0)),
            int(data.get("assignments", 0)),
        )


class PhaseManager:
    """Project-scoped phase helper."""

    DEFAULT_PHASES = ("Existing", "Demolition", "New Construction")

    def __init__(self, project=None):

        self.project = project

    def ensure_default_phases(self):
        """Create default project phases when missing."""

        existing = {phase.name for phase in self.project.phases}

        for index, name in enumerate(self.DEFAULT_PHASES):
            if name not in existing:
                self.project.phases.append(ProjectPhase(name, name, index))

        self.statistics()

        return self.project.phases

    def add_phase(self, phase):
        """Store a project phase."""

        if phase not in self.project.phases:
            self.project.phases.append(phase)

        self.statistics()

        return phase

    def add_sequence(self, sequence):
        """Store a phase sequence."""

        if sequence not in self.project.phase_sequences:
            self.project.phase_sequences.append(sequence)

        self.statistics()

        return sequence

    def add_filter(self, phase_filter):
        """Store a phase visibility filter."""

        if phase_filter not in self.project.phase_filters:
            self.project.phase_filters.append(phase_filter)

        self.statistics()

        return phase_filter

    def add_assignment(self, assignment):
        """Assign an existing BIM element to phases."""

        if assignment not in self.project.phase_assignments:
            self.project.phase_assignments.append(assignment)

        self.statistics()

        return assignment

    def assignment_for(self, item):
        """Return phase assignment for a BIM element."""

        item_id = getattr(item, "id", item)

        return next(
            (assignment for assignment in self.project.phase_assignments if assignment.element_id == item_id),
            None,
        )

    def phase_for(self, phase):
        """Return a project phase by object, id or name."""

        if isinstance(phase, ProjectPhase):
            return phase if phase in self.project.phases else None

        return _find_by_id(self.project.phases, phase)

    def visible_in_filter(self, item, phase_filter=None):
        """Return whether an item is visible under a phase filter."""

        assignment = self.assignment_for(item)

        if assignment is None or phase_filter is None:
            return True

        if phase_filter.visible_phase_ids:
            return assignment.created_phase_id in phase_filter.visible_phase_ids

        phase = self.phase_for(assignment.created_phase_id)
        phase_type = getattr(phase, "phase_type", "")

        if phase_type == "Existing":
            return phase_filter.show_existing
        if phase_type == "Demolition":
            return phase_filter.show_demolition
        if phase_type == "New Construction":
            return phase_filter.show_new

        return True

    def statistics(self):
        """Return phase statistics."""

        stats = PhaseStatistics(
            len(self.project.phases),
            len(self.project.phase_sequences),
            len(self.project.phase_filters),
            len(self.project.phase_assignments),
        )
        self.project.phase_statistics = stats

        return stats


@dataclass
class LifecycleMetadata:
    """Lifecycle metadata."""

    description: str = ""
    responsible_party: str = ""
    properties: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe lifecycle metadata."""

        return {
            "description": self.description,
            "responsible_party": self.responsible_party,
            "properties": dict(self.properties),
        }

    @staticmethod
    def from_dict(data):
        """Create lifecycle metadata from persistence."""

        data = data or {}

        return LifecycleMetadata(
            data.get("description", ""),
            data.get("responsible_party", ""),
            dict(data.get("properties", {})),
        )


@dataclass
class LifecycleState:
    """Lifecycle state assigned to existing BIM elements."""

    name: str = "Planned"
    state_type: str = "Planned"
    metadata: LifecycleMetadata = field(default_factory=LifecycleMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe lifecycle state data."""

        return {
            "id": self.id,
            "name": self.name,
            "state_type": self.state_type,
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create lifecycle state from persistence."""

        data = data or {}

        return LifecycleState(
            data.get("name", "Planned"),
            data.get("state_type", "Planned"),
            LifecycleMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class LifecycleEvent:
    """Lifecycle history event referencing an existing BIM element."""

    element_id: str = ""
    state_id: str = ""
    event_type: str = "State Change"
    timestamp: str = ""
    metadata: LifecycleMetadata = field(default_factory=LifecycleMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe lifecycle event data."""

        return {
            "id": self.id,
            "element_id": self.element_id,
            "state_id": self.state_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create lifecycle event from persistence."""

        data = data or {}

        return LifecycleEvent(
            data.get("element_id", ""),
            data.get("state_id", ""),
            data.get("event_type", "State Change"),
            data.get("timestamp", ""),
            LifecycleMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class LifecycleStatistics:
    """Lifecycle summary statistics."""

    states: int = 0
    events: int = 0
    assigned_elements: int = 0

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create lifecycle statistics."""

        data = data or {}

        return LifecycleStatistics(
            int(data.get("states", 0)),
            int(data.get("events", 0)),
            int(data.get("assigned_elements", 0)),
        )


class LifecycleManager:
    """Project-scoped lifecycle helper."""

    DEFAULT_STATES = (
        "Planned", "Designed", "Constructed", "Commissioned",
        "Operational", "Renovated", "Demolished",
    )

    def __init__(self, project=None):

        self.project = project

    def ensure_default_states(self):
        """Create default lifecycle states when missing."""

        existing = {state.name for state in self.project.lifecycle_states}

        for name in self.DEFAULT_STATES:
            if name not in existing:
                self.project.lifecycle_states.append(LifecycleState(name, name))

        self.statistics()

        return self.project.lifecycle_states

    def add_state(self, state):
        """Store a lifecycle state."""

        if state not in self.project.lifecycle_states:
            self.project.lifecycle_states.append(state)

        self.statistics()

        return state

    def add_event(self, event):
        """Store a lifecycle event."""

        if event not in self.project.lifecycle_events:
            self.project.lifecycle_events.append(event)

        self.statistics()

        return event

    def events_for(self, item):
        """Return lifecycle events for a BIM element."""

        item_id = getattr(item, "id", item)

        return [
            event for event in self.project.lifecycle_events
            if event.element_id == item_id
        ]

    def current_state_for(self, item):
        """Return the latest lifecycle state for a BIM element."""

        events = self.events_for(item)

        if not events:
            return None

        return _find_by_id(self.project.lifecycle_states, events[-1].state_id)

    def statistics(self):
        """Return lifecycle statistics."""

        assigned = {event.element_id for event in self.project.lifecycle_events}
        stats = LifecycleStatistics(
            len(self.project.lifecycle_states),
            len(self.project.lifecycle_events),
            len(assigned),
        )
        self.project.lifecycle_statistics = stats

        return stats


@dataclass
class RoomMetadata:
    """Professional room metadata."""

    department: str = ""
    occupancy: str = ""
    finish: str = ""
    volume: float = 0.0
    properties: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe room metadata."""

        return {
            "department": self.department,
            "occupancy": self.occupancy,
            "finish": self.finish,
            "volume": self.volume,
            "properties": dict(self.properties),
        }

    @staticmethod
    def from_dict(data):
        """Create room metadata from persistence."""

        data = data or {}

        return RoomMetadata(
            data.get("department", ""),
            data.get("occupancy", ""),
            data.get("finish", ""),
            float(data.get("volume", 0.0)),
            dict(data.get("properties", {})),
        )


@dataclass
class RoomBoundary:
    """Boundary reference for a room using existing BIM element IDs."""

    room_id: str = ""
    boundary_ids: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe room boundary data."""

        return {
            "id": self.id,
            "room_id": self.room_id,
            "boundary_ids": list(self.boundary_ids),
        }

    @staticmethod
    def from_dict(data):
        """Create room boundary data from persistence."""

        data = data or {}

        return RoomBoundary(
            data.get("room_id", ""),
            list(data.get("boundary_ids", [])),
            data.get("id", str(uuid4())),
        )


@dataclass
class Room:
    """Room record referencing existing BIM geometry and boundaries."""

    number: str = ""
    name: str = "Room"
    level_id: str = ""
    element_id: str = ""
    area: float = 0.0
    metadata: RoomMetadata = field(default_factory=RoomMetadata)
    boundary_id: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe room data."""

        return {
            "id": self.id,
            "number": self.number,
            "name": self.name,
            "level_id": self.level_id,
            "element_id": self.element_id,
            "area": self.area,
            "metadata": self.metadata.to_dict(),
            "boundary_id": self.boundary_id,
        }

    @staticmethod
    def from_dict(data):
        """Create room data from persistence."""

        data = data or {}

        return Room(
            data.get("number", ""),
            data.get("name", "Room"),
            data.get("level_id", ""),
            data.get("element_id", ""),
            float(data.get("area", 0.0)),
            RoomMetadata.from_dict(data.get("metadata", {})),
            data.get("boundary_id", ""),
            data.get("id", str(uuid4())),
        )


@dataclass
class RoomStatistics:
    """Room summary statistics."""

    rooms: int = 0
    boundaries: int = 0
    total_area: float = 0.0
    total_volume: float = 0.0

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create room statistics from persistence."""

        data = data or {}

        return RoomStatistics(
            int(data.get("rooms", 0)),
            int(data.get("boundaries", 0)),
            float(data.get("total_area", 0.0)),
            float(data.get("total_volume", 0.0)),
        )


class RoomManager:
    """Project-scoped room helper."""

    def __init__(self, project=None):

        self.project = project

    def add_room(self, room):
        """Store a room."""

        if room not in self.project.rooms:
            self.project.rooms.append(room)

        self.statistics()

        return room

    def add_boundary(self, boundary):
        """Store room boundary references."""

        if boundary not in self.project.room_boundaries:
            self.project.room_boundaries.append(boundary)

        room = self.room_for(boundary.room_id)
        if room is not None:
            room.boundary_id = boundary.id

        self.statistics()

        return boundary

    def room_for(self, room):
        """Return a room by object, id, number or name."""

        if isinstance(room, Room):
            return room if room in self.project.rooms else None

        return _find_by_id(self.project.rooms, room)

    def rooms_for_element(self, item):
        """Return rooms linked to a BIM element."""

        item_id = getattr(item, "id", item)

        return [room for room in self.project.rooms if room.element_id == item_id]

    def boundary_for(self, room):
        """Return boundary references for a room."""

        target = self.room_for(room)

        if target is None:
            return None

        return _find_by_id(self.project.room_boundaries, target.boundary_id)

    def statistics(self):
        """Return room statistics."""

        stats = RoomStatistics(
            len(self.project.rooms),
            len(self.project.room_boundaries),
            sum(room.area for room in self.project.rooms),
            sum(room.metadata.volume for room in self.project.rooms),
        )
        self.project.room_statistics = stats

        return stats


@dataclass
class SpaceMetadata:
    """Professional MEP/analytical space metadata."""

    analytical_type: str = "MEP"
    volume: float = 0.0
    height: float = 0.0
    properties: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe space metadata."""

        return {
            "analytical_type": self.analytical_type,
            "volume": self.volume,
            "height": self.height,
            "properties": dict(self.properties),
        }

    @staticmethod
    def from_dict(data):
        """Create space metadata."""

        data = data or {}

        return SpaceMetadata(
            data.get("analytical_type", "MEP"),
            float(data.get("volume", 0.0)),
            float(data.get("height", 0.0)),
            dict(data.get("properties", {})),
        )


@dataclass
class SpaceBoundary:
    """Boundary reference for a space."""

    space_id: str = ""
    boundary_ids: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe space boundary data."""

        return {
            "id": self.id,
            "space_id": self.space_id,
            "boundary_ids": list(self.boundary_ids),
        }

    @staticmethod
    def from_dict(data):
        """Create space boundary data."""

        data = data or {}

        return SpaceBoundary(
            data.get("space_id", ""),
            list(data.get("boundary_ids", [])),
            data.get("id", str(uuid4())),
        )


@dataclass
class Space:
    """Space record referencing existing BIM geometry and boundaries."""

    name: str = "Space"
    room_id: str = ""
    element_id: str = ""
    area: float = 0.0
    metadata: SpaceMetadata = field(default_factory=SpaceMetadata)
    boundary_id: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe space data."""

        return {
            "id": self.id,
            "name": self.name,
            "room_id": self.room_id,
            "element_id": self.element_id,
            "area": self.area,
            "metadata": self.metadata.to_dict(),
            "boundary_id": self.boundary_id,
        }

    @staticmethod
    def from_dict(data):
        """Create space data from persistence."""

        data = data or {}

        return Space(
            data.get("name", "Space"),
            data.get("room_id", ""),
            data.get("element_id", ""),
            float(data.get("area", 0.0)),
            SpaceMetadata.from_dict(data.get("metadata", {})),
            data.get("boundary_id", ""),
            data.get("id", str(uuid4())),
        )


@dataclass
class SpaceStatistics:
    """Space summary statistics."""

    spaces: int = 0
    boundaries: int = 0
    total_area: float = 0.0
    total_volume: float = 0.0

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create space statistics."""

        data = data or {}

        return SpaceStatistics(
            int(data.get("spaces", 0)),
            int(data.get("boundaries", 0)),
            float(data.get("total_area", 0.0)),
            float(data.get("total_volume", 0.0)),
        )


class SpaceManager:
    """Project-scoped space helper."""

    def __init__(self, project=None):

        self.project = project

    def add_space(self, space):
        """Store a space."""

        if space not in self.project.spaces:
            self.project.spaces.append(space)

        self.statistics()

        return space

    def add_boundary(self, boundary):
        """Store space boundary references."""

        if boundary not in self.project.space_boundaries:
            self.project.space_boundaries.append(boundary)

        space = self.space_for(boundary.space_id)
        if space is not None:
            space.boundary_id = boundary.id

        self.statistics()

        return boundary

    def space_for(self, space):
        """Return a space by object, id or name."""

        if isinstance(space, Space):
            return space if space in self.project.spaces else None

        return _find_by_id(self.project.spaces, space)

    def spaces_for_room(self, room):
        """Return spaces associated with a room."""

        room_id = getattr(room, "id", room)

        return [space for space in self.project.spaces if space.room_id == room_id]

    def spaces_for_element(self, item):
        """Return spaces linked to a BIM element."""

        item_id = getattr(item, "id", item)

        return [space for space in self.project.spaces if space.element_id == item_id]

    def statistics(self):
        """Return space statistics."""

        stats = SpaceStatistics(
            len(self.project.spaces),
            len(self.project.space_boundaries),
            sum(space.area for space in self.project.spaces),
            sum(space.metadata.volume for space in self.project.spaces),
        )
        self.project.space_statistics = stats

        return stats


@dataclass
class ZoneMetadata:
    """Zone metadata."""

    description: str = ""
    zone_type: str = "Functional"
    properties: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe zone metadata."""

        return {
            "description": self.description,
            "zone_type": self.zone_type,
            "properties": dict(self.properties),
        }

    @staticmethod
    def from_dict(data):
        """Create zone metadata."""

        data = data or {}

        return ZoneMetadata(
            data.get("description", ""),
            data.get("zone_type", "Functional"),
            dict(data.get("properties", {})),
        )


@dataclass
class Zone:
    """Zone containing room and space references."""

    name: str = "Zone"
    room_ids: list = field(default_factory=list)
    space_ids: list = field(default_factory=list)
    metadata: ZoneMetadata = field(default_factory=ZoneMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe zone data."""

        return {
            "id": self.id,
            "name": self.name,
            "room_ids": list(self.room_ids),
            "space_ids": list(self.space_ids),
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create zone data from persistence."""

        data = data or {}

        return Zone(
            data.get("name", "Zone"),
            list(data.get("room_ids", [])),
            list(data.get("space_ids", [])),
            ZoneMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class ZoneGroup:
    """Group of zones."""

    name: str = "Zone Group"
    zone_ids: list = field(default_factory=list)
    metadata: ZoneMetadata = field(default_factory=ZoneMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe zone group data."""

        return {
            "id": self.id,
            "name": self.name,
            "zone_ids": list(self.zone_ids),
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create zone group data."""

        data = data or {}

        return ZoneGroup(
            data.get("name", "Zone Group"),
            list(data.get("zone_ids", [])),
            ZoneMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class ZoneStatistics:
    """Zone summary statistics."""

    zones: int = 0
    groups: int = 0
    room_memberships: int = 0
    space_memberships: int = 0

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create zone statistics."""

        data = data or {}

        return ZoneStatistics(
            int(data.get("zones", 0)),
            int(data.get("groups", 0)),
            int(data.get("room_memberships", 0)),
            int(data.get("space_memberships", 0)),
        )


class ZoneManager:
    """Project-scoped zone helper."""

    def __init__(self, project=None):

        self.project = project

    def add_zone(self, zone):
        """Store a zone."""

        if zone not in self.project.zones:
            self.project.zones.append(zone)

        self.statistics()

        return zone

    def add_group(self, group):
        """Store a zone group."""

        if group not in self.project.zone_groups:
            self.project.zone_groups.append(group)

        self.statistics()

        return group

    def zones_for_room(self, room):
        """Return zones containing a room."""

        room_id = getattr(room, "id", room)

        return [zone for zone in self.project.zones if room_id in zone.room_ids]

    def zones_for_space(self, space):
        """Return zones containing a space."""

        space_id = getattr(space, "id", space)

        return [zone for zone in self.project.zones if space_id in zone.space_ids]

    def statistics(self):
        """Return zone statistics."""

        stats = ZoneStatistics(
            len(self.project.zones),
            len(self.project.zone_groups),
            sum(len(zone.room_ids) for zone in self.project.zones),
            sum(len(zone.space_ids) for zone in self.project.zones),
        )
        self.project.zone_statistics = stats

        return stats


@dataclass
class AreaBoundary:
    """Area boundary references existing BIM element IDs."""

    region_id: str = ""
    boundary_ids: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe area boundary data."""

        return {
            "id": self.id,
            "region_id": self.region_id,
            "boundary_ids": list(self.boundary_ids),
        }

    @staticmethod
    def from_dict(data):
        """Create area boundary data."""

        data = data or {}

        return AreaBoundary(
            data.get("region_id", ""),
            list(data.get("boundary_ids", [])),
            data.get("id", str(uuid4())),
        )


@dataclass
class AreaRegion:
    """Area region computed from BIM room/space references."""

    name: str = "Area Region"
    area_type: str = "Gross Area"
    room_ids: list = field(default_factory=list)
    space_ids: list = field(default_factory=list)
    area: float = 0.0
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe area region data."""

        return {
            "id": self.id,
            "name": self.name,
            "area_type": self.area_type,
            "room_ids": list(self.room_ids),
            "space_ids": list(self.space_ids),
            "area": self.area,
        }

    @staticmethod
    def from_dict(data):
        """Create area region data."""

        data = data or {}

        return AreaRegion(
            data.get("name", "Area Region"),
            data.get("area_type", "Gross Area"),
            list(data.get("room_ids", [])),
            list(data.get("space_ids", [])),
            float(data.get("area", 0.0)),
            data.get("id", str(uuid4())),
        )


@dataclass
class AreaSummary:
    """Area analysis summary."""

    gross_area: float = 0.0
    net_area: float = 0.0
    usable_area: float = 0.0
    rentable_area: float = 0.0

    def to_dict(self):
        """Return JSON-safe summary."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create area summary."""

        data = data or {}

        return AreaSummary(
            float(data.get("gross_area", 0.0)),
            float(data.get("net_area", 0.0)),
            float(data.get("usable_area", 0.0)),
            float(data.get("rentable_area", 0.0)),
        )


@dataclass
class AreaStatistics:
    """Area analysis statistics."""

    regions: int = 0
    boundaries: int = 0
    total_area: float = 0.0

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create area statistics."""

        data = data or {}

        return AreaStatistics(
            int(data.get("regions", 0)),
            int(data.get("boundaries", 0)),
            float(data.get("total_area", 0.0)),
        )


class AreaAnalysisManager:
    """Project-scoped area analysis helper."""

    def __init__(self, project=None):

        self.project = project

    def add_region(self, region):
        """Store an area region."""

        if region not in self.project.area_regions:
            self.project.area_regions.append(region)

        self.recalculate()

        return region

    def add_boundary(self, boundary):
        """Store an area boundary."""

        if boundary not in self.project.area_boundaries:
            self.project.area_boundaries.append(boundary)

        self.recalculate()

        return boundary

    def recalculate(self):
        """Recalculate area totals from existing room and space data."""

        rooms_by_id = {room.id: room for room in self.project.rooms}
        spaces_by_id = {space.id: space for space in self.project.spaces}

        for region in self.project.area_regions:
            region.area = sum(rooms_by_id[item].area for item in region.room_ids if item in rooms_by_id)
            region.area += sum(spaces_by_id[item].area for item in region.space_ids if item in spaces_by_id)

        totals = {"gross_area": 0.0, "net_area": 0.0, "usable_area": 0.0, "rentable_area": 0.0}
        for region in self.project.area_regions:
            key = region.area_type.lower().replace(" ", "_")
            if key in totals:
                totals[key] += region.area

        self.project.area_summary = AreaSummary(**totals)
        self.project.area_statistics = AreaStatistics(
            len(self.project.area_regions),
            len(self.project.area_boundaries),
            sum(region.area for region in self.project.area_regions),
        )

        return self.project.area_summary


@dataclass
class MEPMetadata:
    """MEP metadata shared by systems, networks and components."""

    discipline: str = "Mechanical"
    description: str = ""
    status: str = "Coordination"
    properties: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe MEP metadata."""

        return {
            "discipline": self.discipline,
            "description": self.description,
            "status": self.status,
            "properties": dict(self.properties),
        }

    @staticmethod
    def from_dict(data):
        """Create MEP metadata from persistence."""

        data = data or {}

        return MEPMetadata(
            data.get("discipline", "Mechanical"),
            data.get("description", ""),
            data.get("status", "Coordination"),
            dict(data.get("properties", {})),
        )


@dataclass
class MEPSystemType:
    """MEP system type descriptor."""

    name: str = "Mechanical"
    category: str = "Mechanical"
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe system type data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create MEP system type data."""

        data = data or {}

        return MEPSystemType(
            data.get("name", "Mechanical"),
            data.get("category", "Mechanical"),
            data.get("id", str(uuid4())),
        )


@dataclass
class MEPSystem:
    """MEP system foundation referencing existing BIM components."""

    name: str = "MEP System"
    system_type_id: str = ""
    component_ids: list = field(default_factory=list)
    network_ids: list = field(default_factory=list)
    metadata: MEPMetadata = field(default_factory=MEPMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe MEP system data."""

        return {
            "id": self.id,
            "name": self.name,
            "system_type_id": self.system_type_id,
            "component_ids": list(self.component_ids),
            "network_ids": list(self.network_ids),
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create MEP system data from persistence."""

        data = data or {}

        return MEPSystem(
            data.get("name", "MEP System"),
            data.get("system_type_id", ""),
            list(data.get("component_ids", [])),
            list(data.get("network_ids", [])),
            MEPMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class MEPNetwork:
    """MEP network topology placeholder."""

    name: str = "MEP Network"
    system_id: str = ""
    component_ids: list = field(default_factory=list)
    connector_ids: list = field(default_factory=list)
    metadata: MEPMetadata = field(default_factory=MEPMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe MEP network data."""

        return {
            "id": self.id,
            "name": self.name,
            "system_id": self.system_id,
            "component_ids": list(self.component_ids),
            "connector_ids": list(self.connector_ids),
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create MEP network data."""

        data = data or {}

        return MEPNetwork(
            data.get("name", "MEP Network"),
            data.get("system_id", ""),
            list(data.get("component_ids", [])),
            list(data.get("connector_ids", [])),
            MEPMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class MEPComponent:
    """MEP component metadata referencing an existing BIM instance."""

    name: str = "MEP Component"
    element_id: str = ""
    system_id: str = ""
    component_type: str = "Equipment"
    connector_ids: list = field(default_factory=list)
    metadata: MEPMetadata = field(default_factory=MEPMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe MEP component data."""

        return {
            "id": self.id,
            "name": self.name,
            "element_id": self.element_id,
            "system_id": self.system_id,
            "component_type": self.component_type,
            "connector_ids": list(self.connector_ids),
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create MEP component data."""

        data = data or {}

        return MEPComponent(
            data.get("name", "MEP Component"),
            data.get("element_id", ""),
            data.get("system_id", ""),
            data.get("component_type", "Equipment"),
            list(data.get("connector_ids", [])),
            MEPMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class MEPConnector:
    """MEP connector placeholder referencing an existing BIM component."""

    component_id: str = ""
    connector_type: str = "Generic"
    port_ids: list = field(default_factory=list)
    metadata: MEPMetadata = field(default_factory=MEPMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe MEP connector data."""

        return {
            "id": self.id,
            "component_id": self.component_id,
            "connector_type": self.connector_type,
            "port_ids": list(self.port_ids),
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create MEP connector data."""

        data = data or {}

        return MEPConnector(
            data.get("component_id", ""),
            data.get("connector_type", "Generic"),
            list(data.get("port_ids", [])),
            MEPMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class MEPPort:
    """MEP port placeholder."""

    connector_id: str = ""
    name: str = "Port"
    direction: str = "Bidirectional"
    metadata: MEPMetadata = field(default_factory=MEPMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe MEP port data."""

        return {
            "id": self.id,
            "connector_id": self.connector_id,
            "name": self.name,
            "direction": self.direction,
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create MEP port data."""

        data = data or {}

        return MEPPort(
            data.get("connector_id", ""),
            data.get("name", "Port"),
            data.get("direction", "Bidirectional"),
            MEPMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class MEPStatistics:
    """MEP foundation statistics."""

    systems: int = 0
    networks: int = 0
    components: int = 0
    connectors: int = 0

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create MEP statistics."""

        data = data or {}

        return MEPStatistics(
            int(data.get("systems", 0)),
            int(data.get("networks", 0)),
            int(data.get("components", 0)),
            int(data.get("connectors", 0)),
        )


@dataclass
class ConnectorMetadata:
    """Connector coordination metadata."""

    description: str = ""
    status: str = "Placeholder"
    properties: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe connector metadata."""

        return {
            "description": self.description,
            "status": self.status,
            "properties": dict(self.properties),
        }

    @staticmethod
    def from_dict(data):
        """Create connector metadata."""

        data = data or {}

        return ConnectorMetadata(
            data.get("description", ""),
            data.get("status", "Placeholder"),
            dict(data.get("properties", {})),
        )


@dataclass
class ConnectorType:
    """Connector type descriptor."""

    name: str = "Generic"
    discipline: str = "Mechanical"
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe connector type data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create connector type data."""

        data = data or {}

        return ConnectorType(
            data.get("name", "Generic"),
            data.get("discipline", "Mechanical"),
            data.get("id", str(uuid4())),
        )


@dataclass
class Connector:
    """Connector between existing BIM/MEP references."""

    source_id: str = ""
    target_id: str = ""
    connector_type_id: str = ""
    metadata: ConnectorMetadata = field(default_factory=ConnectorMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe connector data."""

        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "connector_type_id": self.connector_type_id,
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create connector data."""

        data = data or {}

        return Connector(
            data.get("source_id", ""),
            data.get("target_id", ""),
            data.get("connector_type_id", ""),
            ConnectorMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class ConnectionRule:
    """MEP connection rule placeholder."""

    name: str = "Connection Rule"
    connector_type_id: str = ""
    allowed_target_type: str = "Generic"
    metadata: ConnectorMetadata = field(default_factory=ConnectorMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe connection rule data."""

        return {
            "id": self.id,
            "name": self.name,
            "connector_type_id": self.connector_type_id,
            "allowed_target_type": self.allowed_target_type,
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create connection rule data."""

        data = data or {}

        return ConnectionRule(
            data.get("name", "Connection Rule"),
            data.get("connector_type_id", ""),
            data.get("allowed_target_type", "Generic"),
            ConnectorMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class NetworkMembership:
    """Membership of a component/connector in a MEP network."""

    network_id: str = ""
    member_id: str = ""
    member_type: str = "Component"
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe network membership data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create network membership data."""

        data = data or {}

        return NetworkMembership(
            data.get("network_id", ""),
            data.get("member_id", ""),
            data.get("member_type", "Component"),
            data.get("id", str(uuid4())),
        )


@dataclass
class SystemMembership:
    """Membership of a component/network in a MEP system."""

    system_id: str = ""
    member_id: str = ""
    member_type: str = "Component"
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe system membership data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create system membership data."""

        data = data or {}

        return SystemMembership(
            data.get("system_id", ""),
            data.get("member_id", ""),
            data.get("member_type", "Component"),
            data.get("id", str(uuid4())),
        )


@dataclass
class ClearanceRequirement:
    """MEP clearance requirement placeholder."""

    name: str = "Clearance Requirement"
    system_id: str = ""
    clearance: float = 0.0
    metadata: MEPMetadata = field(default_factory=MEPMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe clearance data."""

        return {
            "id": self.id,
            "name": self.name,
            "system_id": self.system_id,
            "clearance": self.clearance,
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create clearance requirement data."""

        data = data or {}

        return ClearanceRequirement(
            data.get("name", "Clearance Requirement"),
            data.get("system_id", ""),
            float(data.get("clearance", 0.0)),
            MEPMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class ServiceZone:
    """MEP service zone placeholder referencing rooms/spaces/zones."""

    name: str = "Service Zone"
    system_ids: list = field(default_factory=list)
    room_ids: list = field(default_factory=list)
    space_ids: list = field(default_factory=list)
    zone_ids: list = field(default_factory=list)
    metadata: MEPMetadata = field(default_factory=MEPMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe service zone data."""

        return {
            "id": self.id,
            "name": self.name,
            "system_ids": list(self.system_ids),
            "room_ids": list(self.room_ids),
            "space_ids": list(self.space_ids),
            "zone_ids": list(self.zone_ids),
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create service zone data."""

        data = data or {}

        return ServiceZone(
            data.get("name", "Service Zone"),
            list(data.get("system_ids", [])),
            list(data.get("room_ids", [])),
            list(data.get("space_ids", [])),
            list(data.get("zone_ids", [])),
            MEPMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class CoordinationRule:
    """MEP coordination rule placeholder."""

    name: str = "MEP Coordination Rule"
    system_ids: list = field(default_factory=list)
    rule_type: str = "Coordination"
    metadata: MEPMetadata = field(default_factory=MEPMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe MEP coordination rule data."""

        return {
            "id": self.id,
            "name": self.name,
            "system_ids": list(self.system_ids),
            "rule_type": self.rule_type,
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create MEP coordination rule data."""

        data = data or {}

        return CoordinationRule(
            data.get("name", "MEP Coordination Rule"),
            list(data.get("system_ids", [])),
            data.get("rule_type", "Coordination"),
            MEPMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class MEPCoordinationSettings:
    """MEP coordination settings."""

    clash_ready: bool = True
    routing_placeholder: bool = True
    default_clearance: float = 0.0
    options: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe coordination settings."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create MEP coordination settings."""

        data = data or {}

        return MEPCoordinationSettings(
            bool(data.get("clash_ready", True)),
            bool(data.get("routing_placeholder", True)),
            float(data.get("default_clearance", 0.0)),
            dict(data.get("options", {})),
        )


@dataclass
class MEPCoordinationMetadata:
    """MEP coordination metadata."""

    description: str = ""
    status: str = "Foundation"
    properties: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe coordination metadata."""

        return {
            "description": self.description,
            "status": self.status,
            "properties": dict(self.properties),
        }

    @staticmethod
    def from_dict(data):
        """Create coordination metadata."""

        data = data or {}

        return MEPCoordinationMetadata(
            data.get("description", ""),
            data.get("status", "Foundation"),
            dict(data.get("properties", {})),
        )


@dataclass
class MEPCoordinationStatistics:
    """MEP coordination statistics."""

    rules: int = 0
    clearances: int = 0
    service_zones: int = 0

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create MEP coordination statistics."""

        data = data or {}

        return MEPCoordinationStatistics(
            int(data.get("rules", 0)),
            int(data.get("clearances", 0)),
            int(data.get("service_zones", 0)),
        )


class ConnectorManager:
    """Project-scoped connector helper."""

    def __init__(self, project=None):

        self.project = project

    def add_item(self, item):
        """Store connector topology metadata."""

        collection = None
        if isinstance(item, ConnectorType):
            collection = self.project.connector_types
        elif isinstance(item, Connector):
            collection = self.project.connectors
        elif isinstance(item, ConnectionRule):
            collection = self.project.connection_rules
        elif isinstance(item, NetworkMembership):
            collection = self.project.network_memberships
        elif isinstance(item, SystemMembership):
            collection = self.project.system_memberships

        if collection is not None and item not in collection:
            collection.append(item)

        self._refresh_memberships(item)
        return item

    def connectors_for(self, item):
        """Return connectors touching an item."""

        item_id = getattr(item, "id", item)

        return [
            connector for connector in self.project.connectors
            if item_id in (connector.source_id, connector.target_id)
        ]

    def _refresh_memberships(self, item):
        if isinstance(item, NetworkMembership):
            network = _find_by_id(self.project.mep_networks, item.network_id)
            if network is not None:
                target = network.component_ids if item.member_type == "Component" else network.connector_ids
                if item.member_id not in target:
                    target.append(item.member_id)
        if isinstance(item, SystemMembership):
            system = _find_by_id(self.project.mep_systems, item.system_id)
            if system is not None:
                target = system.component_ids if item.member_type == "Component" else system.network_ids
                if item.member_id not in target:
                    target.append(item.member_id)


class MEPManager:
    """Project-scoped MEP coordination foundation helper."""

    DEFAULT_TYPES = ("Mechanical", "Electrical", "Plumbing", "Fire Protection", "Communication")

    def __init__(self, project=None):

        self.project = project

    def ensure_default_types(self):
        """Create default MEP system types."""

        existing = {item.name for item in self.project.mep_system_types}
        for name in self.DEFAULT_TYPES:
            if name not in existing:
                self.project.mep_system_types.append(MEPSystemType(name, name))
        self.statistics()
        return self.project.mep_system_types

    def add_item(self, item):
        """Store MEP foundation metadata."""

        collection = None
        if isinstance(item, MEPSystemType):
            collection = self.project.mep_system_types
        elif isinstance(item, MEPSystem):
            collection = self.project.mep_systems
        elif isinstance(item, MEPNetwork):
            collection = self.project.mep_networks
        elif isinstance(item, MEPComponent):
            collection = self.project.mep_components
        elif isinstance(item, MEPConnector):
            collection = self.project.mep_connectors
        elif isinstance(item, MEPPort):
            collection = self.project.mep_ports
        elif isinstance(item, CoordinationRule):
            collection = self.project.mep_coordination_rules
        elif isinstance(item, ClearanceRequirement):
            collection = self.project.clearance_requirements
        elif isinstance(item, ServiceZone):
            collection = self.project.service_zones

        if collection is not None and item not in collection:
            collection.append(item)

        self._refresh_links(item)
        self.statistics()
        return item

    def components_for(self, item):
        """Return MEP components linked to an existing BIM item."""

        item_id = getattr(item, "id", item)

        return [
            component for component in self.project.mep_components
            if component.element_id == item_id
        ]

    def systems_for(self, item):
        """Return MEP systems linked to an item through components or membership."""

        item_id = getattr(item, "id", item)
        component_ids = {component.id for component in self.components_for(item)}
        system_ids = {
            component.system_id for component in self.project.mep_components
            if component.id in component_ids and component.system_id
        }
        system_ids.update(
            membership.system_id for membership in self.project.system_memberships
            if membership.member_id in component_ids or membership.member_id == item_id
        )

        return [system for system in self.project.mep_systems if system.id in system_ids]

    def networks_for(self, item):
        """Return MEP networks linked to an item."""

        component_ids = {component.id for component in self.components_for(item)}
        network_ids = {
            membership.network_id for membership in self.project.network_memberships
            if membership.member_id in component_ids or membership.member_id == getattr(item, "id", item)
        }

        return [network for network in self.project.mep_networks if network.id in network_ids]

    def coordination_items_for(self, item):
        """Return MEP coordination records related to an item."""

        system_ids = {system.id for system in self.systems_for(item)}

        return {
            "rules": [rule for rule in self.project.mep_coordination_rules if set(rule.system_ids).intersection(system_ids)],
            "clearances": [clearance for clearance in self.project.clearance_requirements if clearance.system_id in system_ids],
            "service_zones": [zone for zone in self.project.service_zones if set(zone.system_ids).intersection(system_ids)],
        }

    def statistics(self):
        """Return MEP statistics."""

        self.project.mep_statistics = MEPStatistics(
            len(self.project.mep_systems),
            len(self.project.mep_networks),
            len(self.project.mep_components),
            len(self.project.mep_connectors) + len(self.project.connectors),
        )
        self.project.mep_coordination_statistics = MEPCoordinationStatistics(
            len(self.project.mep_coordination_rules),
            len(self.project.clearance_requirements),
            len(self.project.service_zones),
        )
        return self.project.mep_statistics

    def _refresh_links(self, item):
        if isinstance(item, MEPComponent):
            system = _find_by_id(self.project.mep_systems, item.system_id)
            if system is not None and item.id not in system.component_ids:
                system.component_ids.append(item.id)
        if isinstance(item, MEPConnector):
            component = _find_by_id(self.project.mep_components, item.component_id)
            if component is not None and item.id not in component.connector_ids:
                component.connector_ids.append(item.id)
        if isinstance(item, MEPPort):
            connector = _find_by_id(self.project.mep_connectors, item.connector_id)
            if connector is not None and item.id not in connector.port_ids:
                connector.port_ids.append(item.id)


@dataclass
class ValidationSeverity:
    """Validation severity descriptor."""

    name: str = "Warning"
    level: int = 1
    color: str = "#ffb300"
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe severity data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create severity data."""

        data = data or {}

        return ValidationSeverity(
            data.get("name", "Warning"),
            int(data.get("level", 1)),
            data.get("color", "#ffb300"),
            data.get("id", str(uuid4())),
        )


@dataclass
class ValidationMetadata:
    """Validation metadata."""

    description: str = ""
    source: str = "BIM"
    properties: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe validation metadata."""

        return {
            "description": self.description,
            "source": self.source,
            "properties": dict(self.properties),
        }

    @staticmethod
    def from_dict(data):
        """Create validation metadata."""

        data = data or {}

        return ValidationMetadata(
            data.get("description", ""),
            data.get("source", "BIM"),
            dict(data.get("properties", {})),
        )


@dataclass
class ValidationCategory:
    """Validation category descriptor."""

    name: str = "General"
    metadata: ValidationMetadata = field(default_factory=ValidationMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe category data."""

        return {"id": self.id, "name": self.name, "metadata": self.metadata.to_dict()}

    @staticmethod
    def from_dict(data):
        """Create validation category."""

        data = data or {}

        return ValidationCategory(
            data.get("name", "General"),
            ValidationMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class ValidationRule:
    """BIM validation rule definition."""

    name: str = "Validation Rule"
    rule_type: str = "Missing Data"
    category_id: str = ""
    severity: str = "Warning"
    required_field: str = ""
    metadata: ValidationMetadata = field(default_factory=ValidationMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe validation rule data."""

        return {
            "id": self.id,
            "name": self.name,
            "rule_type": self.rule_type,
            "category_id": self.category_id,
            "severity": self.severity,
            "required_field": self.required_field,
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create validation rule."""

        data = data or {}

        return ValidationRule(
            data.get("name", "Validation Rule"),
            data.get("rule_type", "Missing Data"),
            data.get("category_id", ""),
            data.get("severity", "Warning"),
            data.get("required_field", ""),
            ValidationMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class ValidationResult:
    """Validation result referencing an existing BIM item."""

    rule_id: str = ""
    target_id: str = ""
    message: str = ""
    severity: str = "Warning"
    passed: bool = False
    metadata: ValidationMetadata = field(default_factory=ValidationMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe validation result data."""

        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "target_id": self.target_id,
            "message": self.message,
            "severity": self.severity,
            "passed": self.passed,
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create validation result."""

        data = data or {}

        return ValidationResult(
            data.get("rule_id", ""),
            data.get("target_id", ""),
            data.get("message", ""),
            data.get("severity", "Warning"),
            bool(data.get("passed", False)),
            ValidationMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class ValidationProfile:
    """Reusable validation profile."""

    name: str = "BIM Validation Profile"
    rule_ids: list = field(default_factory=list)
    metadata: ValidationMetadata = field(default_factory=ValidationMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe profile data."""

        return {
            "id": self.id,
            "name": self.name,
            "rule_ids": list(self.rule_ids),
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create validation profile."""

        data = data or {}

        return ValidationProfile(
            data.get("name", "BIM Validation Profile"),
            list(data.get("rule_ids", [])),
            ValidationMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class ValidationStatistics:
    """Validation summary statistics."""

    rules: int = 0
    profiles: int = 0
    results: int = 0
    failures: int = 0

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create validation statistics."""

        data = data or {}

        return ValidationStatistics(
            int(data.get("rules", 0)),
            int(data.get("profiles", 0)),
            int(data.get("results", 0)),
            int(data.get("failures", 0)),
        )


class ValidationManager:
    """Project-scoped BIM validation helper."""

    def __init__(self, project=None):

        self.project = project

    def add_item(self, item):
        """Store validation metadata."""

        collection = None
        if isinstance(item, ValidationRule):
            collection = self.project.validation_rules
        elif isinstance(item, ValidationCategory):
            collection = self.project.validation_categories
        elif isinstance(item, ValidationResult):
            collection = self.project.validation_results
        elif isinstance(item, ValidationProfile):
            collection = self.project.validation_profiles
        elif isinstance(item, ValidationSeverity):
            collection = self.project.validation_severities

        if collection is not None and item not in collection:
            collection.append(item)

        self.statistics()
        return item

    def run(self, profile=None):
        """Run foundation validation against existing BIM data."""

        rule_ids = set(getattr(profile, "rule_ids", [])) if profile is not None else None
        rules = [
            rule for rule in self.project.validation_rules
            if rule_ids is None or rule.id in rule_ids
        ]
        self.project.validation_results = []

        for rule in rules:
            for instance in self.project.instances:
                result = self._evaluate_rule(rule, instance)
                if result is not None:
                    self.project.validation_results.append(result)

        self.statistics()
        return self.project.validation_results

    def results_for(self, item):
        """Return validation results for a BIM item."""

        item_id = getattr(item, "id", item)

        return [result for result in self.project.validation_results if result.target_id == item_id]

    def statistics(self):
        """Return validation statistics."""

        stats = ValidationStatistics(
            len(self.project.validation_rules),
            len(self.project.validation_profiles),
            len(self.project.validation_results),
            len([result for result in self.project.validation_results if not result.passed]),
        )
        self.project.validation_statistics = stats
        return stats

    def _evaluate_rule(self, rule, instance):
        rule_type = rule.rule_type.lower()
        passed = True
        message = ""

        if rule_type == "required property":
            passed = bool(_bim_field_value(instance, rule.required_field))
            message = f"Required property missing: {rule.required_field}"
        elif rule_type == "missing data":
            passed = bool(getattr(instance, "name", "")) and bool(getattr(instance, "element_definition_id", ""))
            message = "Missing required BIM data"
        elif rule_type == "relationship":
            passed = bool(self.project.relationships)
            message = "No relationship graph data"
        elif rule_type == "host/opening":
            passed = bool(self.project.host_objects or self.project.openings)
            message = "No host/opening data"
        elif rule_type == "classification":
            passed = any(mapping.target_id == instance.id for mapping in self.project.classification_mappings)
            message = "Missing classification"
        elif rule_type == "ifc readiness":
            passed = any(element.bim_instance_id == instance.id for element in self.project.ifc_elements)
            message = "Missing IFC mapping"
        elif rule_type == "schedule":
            passed = any(any(row.source_id == instance.id for row in schedule.rows) for schedule in self.project.schedules)
            message = "Missing schedule row"

        if passed:
            return None

        return ValidationResult(rule.id, instance.id, message, rule.severity, False)


@dataclass
class ModelCheckRule:
    """Model checking rule definition."""

    name: str = "Model Check Rule"
    check_type: str = "Invalid References"
    metadata: ValidationMetadata = field(default_factory=ValidationMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe model check rule data."""

        return {
            "id": self.id,
            "name": self.name,
            "check_type": self.check_type,
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create model check rule."""

        data = data or {}

        return ModelCheckRule(
            data.get("name", "Model Check Rule"),
            data.get("check_type", "Invalid References"),
            ValidationMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class ModelCheckResult:
    """Model check result referencing existing BIM data."""

    rule_id: str = ""
    target_id: str = ""
    message: str = ""
    passed: bool = False
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe model check result data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create model check result."""

        data = data or {}

        return ModelCheckResult(
            data.get("rule_id", ""),
            data.get("target_id", ""),
            data.get("message", ""),
            bool(data.get("passed", False)),
            data.get("id", str(uuid4())),
        )


@dataclass
class ModelCheckProfile:
    """Reusable model check profile."""

    name: str = "Model Check Profile"
    rule_ids: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe model check profile data."""

        return {"id": self.id, "name": self.name, "rule_ids": list(self.rule_ids)}

    @staticmethod
    def from_dict(data):
        """Create model check profile."""

        data = data or {}

        return ModelCheckProfile(
            data.get("name", "Model Check Profile"),
            list(data.get("rule_ids", [])),
            data.get("id", str(uuid4())),
        )


@dataclass
class ModelCheckStatistics:
    """Model check statistics."""

    rules: int = 0
    profiles: int = 0
    results: int = 0
    failures: int = 0

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create model check statistics."""

        data = data or {}

        return ModelCheckStatistics(
            int(data.get("rules", 0)),
            int(data.get("profiles", 0)),
            int(data.get("results", 0)),
            int(data.get("failures", 0)),
        )


class ModelCheckManager:
    """Project-scoped model checking helper."""

    def __init__(self, project=None):

        self.project = project

    def add_item(self, item):
        """Store model check metadata."""

        collection = None
        if isinstance(item, ModelCheckRule):
            collection = self.project.model_check_rules
        elif isinstance(item, ModelCheckProfile):
            collection = self.project.model_check_profiles
        elif isinstance(item, ModelCheckResult):
            collection = self.project.model_check_results

        if collection is not None and item not in collection:
            collection.append(item)

        self.statistics()
        return item

    def run(self, profile=None):
        """Run foundation model checks against existing BIM data."""

        rule_ids = set(getattr(profile, "rule_ids", [])) if profile is not None else None
        rules = [
            rule for rule in self.project.model_check_rules
            if rule_ids is None or rule.id in rule_ids
        ]
        self.project.model_check_results = []

        for rule in rules:
            self.project.model_check_results.extend(self._evaluate_rule(rule))

        self.statistics()
        return self.project.model_check_results

    def results_for(self, item):
        """Return model check results for a BIM item."""

        item_id = getattr(item, "id", item)

        return [result for result in self.project.model_check_results if result.target_id == item_id]

    def statistics(self):
        """Return model check statistics."""

        stats = ModelCheckStatistics(
            len(self.project.model_check_rules),
            len(self.project.model_check_profiles),
            len(self.project.model_check_results),
            len([result for result in self.project.model_check_results if not result.passed]),
        )
        self.project.model_check_statistics = stats
        return stats

    def _evaluate_rule(self, rule):
        check_type = rule.check_type.lower()
        results = []

        if check_type == "duplicate element detection":
            seen = {}
            for instance in self.project.instances:
                key = (instance.name, instance.mesh_entity_id)
                if key in seen:
                    results.append(ModelCheckResult(rule.id, instance.id, "Duplicate element", False))
                seen[key] = instance.id
        elif check_type == "orphan element detection":
            for instance in self.project.instances:
                if not instance.level_id and not instance.building_id:
                    results.append(ModelCheckResult(rule.id, instance.id, "Orphan element", False))
        elif check_type in ("invalid references", "invalid relationships"):
            ids = {instance.id for instance in self.project.instances}
            for relationship in self.project.relationships:
                if relationship.source_id not in ids or relationship.target_id not in ids:
                    results.append(ModelCheckResult(rule.id, relationship.id, "Invalid relationship reference", False))
        elif check_type == "missing materials":
            for instance in self.project.instances:
                if not getattr(instance, "material_assignment_id", ""):
                    results.append(ModelCheckResult(rule.id, instance.id, "Missing material", False))
        elif check_type == "missing classifications":
            mapped = {mapping.target_id for mapping in self.project.classification_mappings}
            for instance in self.project.instances:
                if instance.id not in mapped:
                    results.append(ModelCheckResult(rule.id, instance.id, "Missing classification", False))
        elif check_type == "missing levels":
            for instance in self.project.instances:
                if not getattr(instance, "level_id", ""):
                    results.append(ModelCheckResult(rule.id, instance.id, "Missing level", False))
        elif check_type == "missing rooms":
            room_elements = {room.element_id for room in self.project.rooms}
            for instance in self.project.instances:
                if instance.id not in room_elements:
                    results.append(ModelCheckResult(rule.id, instance.id, "Missing room assignment", False))

        return results


@dataclass
class ExchangeMetadata:
    """Interoperability exchange metadata."""

    description: str = ""
    target: str = "IFC"
    properties: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe exchange metadata."""

        return {
            "description": self.description,
            "target": self.target,
            "properties": dict(self.properties),
        }

    @staticmethod
    def from_dict(data):
        """Create exchange metadata."""

        data = data or {}

        return ExchangeMetadata(
            data.get("description", ""),
            data.get("target", "IFC"),
            dict(data.get("properties", {})),
        )


@dataclass
class ExchangeRule:
    """Interoperability exchange rule."""

    name: str = "Exchange Rule"
    rule_type: str = "IFC readiness"
    metadata: ExchangeMetadata = field(default_factory=ExchangeMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe exchange rule data."""

        return {
            "id": self.id,
            "name": self.name,
            "rule_type": self.rule_type,
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create exchange rule."""

        data = data or {}

        return ExchangeRule(
            data.get("name", "Exchange Rule"),
            data.get("rule_type", "IFC readiness"),
            ExchangeMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class ExchangeProfile:
    """Interoperability exchange profile."""

    name: str = "Exchange Profile"
    rule_ids: list = field(default_factory=list)
    metadata: ExchangeMetadata = field(default_factory=ExchangeMetadata)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe exchange profile data."""

        return {
            "id": self.id,
            "name": self.name,
            "rule_ids": list(self.rule_ids),
            "metadata": self.metadata.to_dict(),
        }

    @staticmethod
    def from_dict(data):
        """Create exchange profile."""

        data = data or {}

        return ExchangeProfile(
            data.get("name", "Exchange Profile"),
            list(data.get("rule_ids", [])),
            ExchangeMetadata.from_dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class ExchangeStatistics:
    """Interoperability statistics."""

    profiles: int = 0
    rules: int = 0
    ready_targets: int = 0
    blocked_targets: int = 0

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create exchange statistics."""

        data = data or {}

        return ExchangeStatistics(
            int(data.get("profiles", 0)),
            int(data.get("rules", 0)),
            int(data.get("ready_targets", 0)),
            int(data.get("blocked_targets", 0)),
        )


class InteroperabilityManager:
    """Project-scoped BIM interoperability readiness helper."""

    def __init__(self, project=None):

        self.project = project

    def add_item(self, item):
        """Store interoperability metadata."""

        collection = None
        if isinstance(item, ExchangeProfile):
            collection = self.project.exchange_profiles
        elif isinstance(item, ExchangeRule):
            collection = self.project.exchange_rules

        if collection is not None and item not in collection:
            collection.append(item)

        self.statistics()
        return item

    def readiness(self):
        """Return exchange readiness based on existing BIM managers."""

        return {
            "IFC": bool(self.project.ifc_elements),
            "BCF": True,
            "Reference": True,
            "CAD": bool(self.project.instances),
            "ImportExport": bool(self.project.instances),
        }

    def statistics(self):
        """Return interoperability statistics."""

        readiness = self.readiness()
        stats = ExchangeStatistics(
            len(self.project.exchange_profiles),
            len(self.project.exchange_rules),
            len([value for value in readiness.values() if value]),
            len([value for value in readiness.values() if not value]),
        )
        self.project.exchange_statistics = stats
        return stats


@dataclass
class BIMCategory:
    """BIM category metadata wrapper."""

    name: str = "Generic Model"
    discipline: str = "Architecture"
    description: str = ""
    color: str = "#b0bec5"
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe category data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create category data from persistence."""

        data = data or {}

        return BIMCategory(
            data.get("name", "Generic Model"),
            data.get("discipline", "Architecture"),
            data.get("description", ""),
            data.get("color", "#b0bec5"),
            data.get("id", str(uuid4())),
        )


@dataclass
class BIMType:
    """BIM type metadata wrapper."""

    name: str = "Generic Type"
    category_id: str = ""
    parameters: dict = field(default_factory=dict)
    classification: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    family_id: str = ""
    element_definition_id: str = ""
    type_parameters: TypeParameters = field(default_factory=TypeParameters)
    type_defaults: TypeDefaults = field(default_factory=TypeDefaults)
    property_set_ids: list = field(default_factory=list)

    def to_dict(self):
        """Return JSON-safe type data."""

        return {
            "id": self.id,
            "name": self.name,
            "category_id": self.category_id,
            "family_id": self.family_id,
            "element_definition_id": self.element_definition_id,
            "parameters": dict(self.parameters),
            "classification": dict(self.classification),
            "type_parameters": self.type_parameters.to_dict(),
            "type_defaults": self.type_defaults.to_dict(),
            "property_set_ids": list(self.property_set_ids),
        }

    @staticmethod
    def from_dict(data):
        """Create BIM type data from persistence."""

        data = data or {}
        item = BIMType(
            data.get("name", "Generic Type"),
            data.get("category_id", ""),
            dict(data.get("parameters", {})),
            dict(data.get("classification", {})),
            data.get("id", str(uuid4())),
        )
        item.family_id = data.get("family_id", "")
        item.element_definition_id = data.get("element_definition_id", "")
        item.type_parameters = TypeParameters.from_dict(data.get("type_parameters", item.parameters))
        item.type_defaults = TypeDefaults.from_dict(data.get("type_defaults", {}))
        item.property_set_ids = list(data.get("property_set_ids", []))

        return item


class BIMObject:
    """Base metadata object for BIM items that reference existing geometry."""

    type_name = "BIMObject"
    is_3d = True
    is_bim = True

    def __init__(self, name="BIM Object", category_id="", type_id="", location=None):

        self.id = str(uuid4())
        self.guid = str(uuid4())
        self.name = name
        self.category_id = category_id
        self.type_id = type_id
        self.classification = {}
        self.property_sets = {}
        self.relationships = {}
        self.level_id = ""
        self.building_id = ""
        self.mesh_entity_id = ""
        self.mesh_entity_name = ""
        self.family_id = ""
        self.element_definition_id = ""
        self.instance_parameters = InstanceParameters()
        self.instance_overrides = InstanceOverrides()
        self.element_parameters = ElementParameters()
        self.element_relationships = ElementRelationships()
        self.material_assignment_id = ""
        self.assembly_ids = []
        self.property_set_ids = []
        self.location = location or Vector3()
        self.visible = True
        self.locked = False
        self.selected = False
        self.hovered = False
        self.layer_name = None
        self.color = None
        self.entity = None

    @property
    def display_color(self):
        """Return object display color without owning geometry style."""

        return self.color or getattr(self.entity, "display_color", "#b0bec5")

    @property
    def bounding_box3d(self):
        """Return referenced entity bounds or compact metadata bounds."""

        if self.entity is not None and getattr(self.entity, "bounding_box3d", None).valid:
            return self.entity.bounding_box3d

        box = BoundingBox3D()
        pad = 6.0
        box.add(self.location - Vector3(pad, pad, pad))
        box.add(self.location + Vector3(pad, pad, pad))

        return box

    def points(self):
        """Return representative object points."""

        if self.entity is not None:
            return self.entity.points()

        return [self.location]

    def segments(self):
        """Return referenced geometry wire segments or a compact marker."""

        if self.entity is not None:
            return self.entity.segments()

        pad = 6.0
        a = self.location + Vector3(-pad, 0.0, 0.0)
        b = self.location + Vector3(pad, 0.0, 0.0)
        c = self.location + Vector3(0.0, -pad, 0.0)
        d = self.location + Vector3(0.0, pad, 0.0)
        e = self.location + Vector3(0.0, 0.0, -pad)
        f = self.location + Vector3(0.0, 0.0, pad)

        return [(a, b), (c, d), (e, f)]

    def to_dict(self):
        """Return JSON-safe BIM object metadata."""

        return {
            "id": self.id,
            "guid": self.guid,
            "name": self.name,
            "category_id": self.category_id,
            "type_id": self.type_id,
            "classification": dict(self.classification),
            "property_sets": dict(self.property_sets),
            "relationships": dict(self.relationships),
            "level_id": self.level_id,
            "building_id": self.building_id,
            "mesh_entity_id": self.mesh_entity_id,
            "mesh_entity_name": self.mesh_entity_name,
            "family_id": self.family_id,
            "element_definition_id": self.element_definition_id,
            "instance_parameters": self.instance_parameters.to_dict(),
            "instance_overrides": self.instance_overrides.to_dict(),
            "element_parameters": self.element_parameters.to_dict(),
            "element_relationships": self.element_relationships.to_dict(),
            "material_assignment_id": self.material_assignment_id,
            "assembly_ids": list(self.assembly_ids),
            "property_set_ids": list(self.property_set_ids),
            "location": _vector_to_data(self.location),
            "visible": self.visible,
            "locked": self.locked,
            "selected": self.selected,
            "layer_name": self.layer_name,
            "color": self.color,
        }

    @classmethod
    def from_dict(cls, data):
        """Create a BIM object from persisted metadata."""

        data = data or {}
        item = cls(
            data.get("name", "BIM Object"),
            data.get("category_id", ""),
            data.get("type_id", ""),
            _vector_from_data(data.get("location")),
        )
        item.id = data.get("id", item.id)
        item.guid = data.get("guid", item.guid)
        item.classification = dict(data.get("classification", {}))
        item.property_sets = dict(data.get("property_sets", {}))
        item.relationships = dict(data.get("relationships", {}))
        item.level_id = data.get("level_id", "")
        item.building_id = data.get("building_id", "")
        item.mesh_entity_id = data.get("mesh_entity_id", "")
        item.mesh_entity_name = data.get("mesh_entity_name", "")
        item.family_id = data.get("family_id", "")
        item.element_definition_id = data.get("element_definition_id", "")
        item.instance_parameters = InstanceParameters.from_dict(data.get("instance_parameters", {}))
        item.instance_overrides = InstanceOverrides.from_dict(data.get("instance_overrides", {}))
        item.element_parameters = ElementParameters.from_dict(data.get("element_parameters", {}))
        item.element_relationships = ElementRelationships.from_dict(data.get("element_relationships", {}))
        item.material_assignment_id = data.get("material_assignment_id", "")
        item.assembly_ids = list(data.get("assembly_ids", []))
        item.property_set_ids = list(data.get("property_set_ids", []))
        item.visible = bool(data.get("visible", True))
        item.locked = bool(data.get("locked", False))
        item.selected = bool(data.get("selected", False))
        item.layer_name = data.get("layer_name")
        item.color = data.get("color")

        return item


class BIMInstance(BIMObject):
    """BIM instance metadata linked to existing 3D entity geometry."""

    type_name = "BIMInstance"

    def __init__(self, name="BIM Instance", category_id="", type_id="", entity=None, location=None):

        super().__init__(name, category_id, type_id, location)
        self.entity = entity

        if entity is not None:
            self.mesh_entity_id = getattr(entity, "id", getattr(entity, "name", ""))
            self.mesh_entity_name = getattr(entity, "name", "")
            self.layer_name = getattr(entity, "layer_name", None)

    @staticmethod
    def from_dict(data):
        """Create a BIM instance from persisted metadata."""

        data = data or {}
        instance = BIMInstance(
            data.get("name", "BIM Instance"),
            data.get("category_id", ""),
            data.get("type_id", ""),
            None,
            _vector_from_data(data.get("location")),
        )
        instance.id = data.get("id", instance.id)
        instance.guid = data.get("guid", instance.guid)
        instance.classification = dict(data.get("classification", {}))
        instance.property_sets = dict(data.get("property_sets", {}))
        instance.relationships = dict(data.get("relationships", {}))
        instance.level_id = data.get("level_id", "")
        instance.building_id = data.get("building_id", "")
        instance.mesh_entity_id = data.get("mesh_entity_id", "")
        instance.mesh_entity_name = data.get("mesh_entity_name", "")
        instance.family_id = data.get("family_id", "")
        instance.element_definition_id = data.get("element_definition_id", "")
        instance.instance_parameters = InstanceParameters.from_dict(data.get("instance_parameters", {}))
        instance.instance_overrides = InstanceOverrides.from_dict(data.get("instance_overrides", {}))
        instance.element_parameters = ElementParameters.from_dict(data.get("element_parameters", {}))
        instance.element_relationships = ElementRelationships.from_dict(data.get("element_relationships", {}))
        instance.material_assignment_id = data.get("material_assignment_id", "")
        instance.assembly_ids = list(data.get("assembly_ids", []))
        instance.property_set_ids = list(data.get("property_set_ids", []))
        instance.visible = bool(data.get("visible", True))
        instance.locked = bool(data.get("locked", False))
        instance.selected = bool(data.get("selected", False))
        instance.layer_name = data.get("layer_name")
        instance.color = data.get("color")

        return instance


class BIMProject:
    """Workspace-owned BIM project container."""

    def __init__(self, name="BIM Project", metadata=None, settings=None):

        self.id = str(uuid4())
        self.name = name
        self.metadata = (
            metadata
            if isinstance(metadata, BuildingMetadata)
            else BuildingMetadata.from_dict(metadata or {})
        )
        self.settings = (
            settings
            if isinstance(settings, BIMSettings)
            else BIMSettings.from_dict(settings or {})
        )
        self.sites = []
        self.buildings = []
        self.levels = []
        self.level_definitions = []
        self.level_groups = []
        self.grids = []
        self.grid_lines = []
        self.grid_intersections = []
        self.grid_groups = []
        self.grid_statistics = GridStatistics()
        self.views = []
        self.view_templates = []
        self.view_statistics = ViewStatistics()
        self.sheets = []
        self.documentation_settings = DocumentationSettings()
        self.schedules = []
        self.schedule_templates = []
        self.schedule_statistics = ScheduleStatistics()
        self.classification_systems = []
        self.classification_mappings = []
        self.classification_statistics = ClassificationStatistics()
        self.ifc_project = None
        self.ifc_sites = []
        self.ifc_buildings = []
        self.ifc_storeys = []
        self.ifc_elements = []
        self.ifc_relationships = []
        self.ifc_property_sets = []
        self.ifc_export_settings = IFCExportSettings()
        self.ifc_import_settings = IFCImportSettings()
        self.ifc_metadata = IFCMetadata()
        self.relationship_types = []
        self.relationships = []
        self.relationship_statistics = RelationshipStatistics()
        self.host_objects = []
        self.hosted_objects = []
        self.openings = []
        self.voids = []
        self.cut_relationships = []
        self.connection_types = []
        self.connections = []
        self.connection_statistics = ConnectionStatistics()
        self.design_option_sets = []
        self.design_options = []
        self.option_memberships = []
        self.option_statistics = OptionStatistics()
        self.phases = []
        self.phase_sequences = []
        self.phase_filters = []
        self.phase_assignments = []
        self.phase_statistics = PhaseStatistics()
        self.lifecycle_states = []
        self.lifecycle_events = []
        self.lifecycle_statistics = LifecycleStatistics()
        self.rooms = []
        self.room_boundaries = []
        self.room_statistics = RoomStatistics()
        self.spaces = []
        self.space_boundaries = []
        self.space_statistics = SpaceStatistics()
        self.zones = []
        self.zone_groups = []
        self.zone_statistics = ZoneStatistics()
        self.area_regions = []
        self.area_boundaries = []
        self.area_summary = AreaSummary()
        self.area_statistics = AreaStatistics()
        self.mep_system_types = []
        self.mep_systems = []
        self.mep_networks = []
        self.mep_components = []
        self.mep_connectors = []
        self.mep_ports = []
        self.mep_statistics = MEPStatistics()
        self.connector_types = []
        self.connectors = []
        self.connection_rules = []
        self.network_memberships = []
        self.system_memberships = []
        self.mep_coordination_rules = []
        self.clearance_requirements = []
        self.service_zones = []
        self.mep_coordination_settings = MEPCoordinationSettings()
        self.mep_coordination_metadata = MEPCoordinationMetadata()
        self.mep_coordination_statistics = MEPCoordinationStatistics()
        self.validation_severities = []
        self.validation_categories = []
        self.validation_rules = []
        self.validation_profiles = []
        self.validation_results = []
        self.validation_statistics = ValidationStatistics()
        self.model_check_rules = []
        self.model_check_profiles = []
        self.model_check_results = []
        self.model_check_statistics = ModelCheckStatistics()
        self.exchange_profiles = []
        self.exchange_rules = []
        self.exchange_statistics = ExchangeStatistics()
        self.categories = []
        self.family_categories = []
        self.families = []
        self.element_categories = []
        self.element_definitions = []
        self.material_categories = []
        self.materials = []
        self.material_assignments = []
        self.material_layer_sets = []
        self.assembly_types = []
        self.assemblies = []
        self.assembly_templates = []
        self.quantity_rules = []
        self.quantity_items = []
        self.quantity_summary = QuantitySummary()
        self.quantity_statistics = QuantityStatistics()
        self.types = []
        self.instances = []
        self.property_sets = []

    def to_dict(self):
        """Return JSON-safe BIM project data."""

        return {
            "id": self.id,
            "name": self.name,
            "metadata": self.metadata.to_dict(),
            "settings": self.settings.to_dict(),
            "sites": [site.to_dict() for site in self.sites],
            "buildings": [building.to_dict() for building in self.buildings],
            "levels": [level.to_dict() for level in self.levels],
            "level_definitions": [definition.to_dict() for definition in self.level_definitions],
            "level_groups": [group.to_dict() for group in self.level_groups],
            "grids": [grid.to_dict() for grid in self.grids],
            "grid_lines": [line.to_dict() for line in self.grid_lines],
            "grid_intersections": [intersection.to_dict() for intersection in self.grid_intersections],
            "grid_groups": [group.to_dict() for group in self.grid_groups],
            "grid_statistics": self.grid_statistics.to_dict(),
            "views": [view.to_dict() for view in self.views],
            "view_templates": [template.to_dict() for template in self.view_templates],
            "view_statistics": self.view_statistics.to_dict(),
            "sheets": [sheet.to_dict() for sheet in self.sheets],
            "documentation_settings": self.documentation_settings.to_dict(),
            "schedules": [schedule.to_dict() for schedule in self.schedules],
            "schedule_templates": [schedule.to_dict() for schedule in self.schedule_templates],
            "schedule_statistics": self.schedule_statistics.to_dict(),
            "classification_systems": [system.to_dict() for system in self.classification_systems],
            "classification_mappings": [mapping.to_dict() for mapping in self.classification_mappings],
            "classification_statistics": self.classification_statistics.to_dict(),
            "ifc_project": self.ifc_project.to_dict() if self.ifc_project is not None else None,
            "ifc_sites": [item.to_dict() for item in self.ifc_sites],
            "ifc_buildings": [item.to_dict() for item in self.ifc_buildings],
            "ifc_storeys": [item.to_dict() for item in self.ifc_storeys],
            "ifc_elements": [item.to_dict() for item in self.ifc_elements],
            "ifc_relationships": [item.to_dict() for item in self.ifc_relationships],
            "ifc_property_sets": [item.to_dict() for item in self.ifc_property_sets],
            "ifc_export_settings": self.ifc_export_settings.to_dict(),
            "ifc_import_settings": self.ifc_import_settings.to_dict(),
            "ifc_metadata": self.ifc_metadata.to_dict(),
            "relationship_types": [item.to_dict() for item in self.relationship_types],
            "relationships": [item.to_dict() for item in self.relationships],
            "relationship_statistics": self.relationship_statistics.to_dict(),
            "host_objects": [item.to_dict() for item in self.host_objects],
            "hosted_objects": [item.to_dict() for item in self.hosted_objects],
            "openings": [item.to_dict() for item in self.openings],
            "voids": [item.to_dict() for item in self.voids],
            "cut_relationships": [item.to_dict() for item in self.cut_relationships],
            "connection_types": [item.to_dict() for item in self.connection_types],
            "connections": [item.to_dict() for item in self.connections],
            "connection_statistics": self.connection_statistics.to_dict(),
            "design_option_sets": [item.to_dict() for item in self.design_option_sets],
            "design_options": [item.to_dict() for item in self.design_options],
            "option_memberships": [item.to_dict() for item in self.option_memberships],
            "option_statistics": self.option_statistics.to_dict(),
            "phases": [item.to_dict() for item in self.phases],
            "phase_sequences": [item.to_dict() for item in self.phase_sequences],
            "phase_filters": [item.to_dict() for item in self.phase_filters],
            "phase_assignments": [item.to_dict() for item in self.phase_assignments],
            "phase_statistics": self.phase_statistics.to_dict(),
            "lifecycle_states": [item.to_dict() for item in self.lifecycle_states],
            "lifecycle_events": [item.to_dict() for item in self.lifecycle_events],
            "lifecycle_statistics": self.lifecycle_statistics.to_dict(),
            "rooms": [item.to_dict() for item in self.rooms],
            "room_boundaries": [item.to_dict() for item in self.room_boundaries],
            "room_statistics": self.room_statistics.to_dict(),
            "spaces": [item.to_dict() for item in self.spaces],
            "space_boundaries": [item.to_dict() for item in self.space_boundaries],
            "space_statistics": self.space_statistics.to_dict(),
            "zones": [item.to_dict() for item in self.zones],
            "zone_groups": [item.to_dict() for item in self.zone_groups],
            "zone_statistics": self.zone_statistics.to_dict(),
            "area_regions": [item.to_dict() for item in self.area_regions],
            "area_boundaries": [item.to_dict() for item in self.area_boundaries],
            "area_summary": self.area_summary.to_dict(),
            "area_statistics": self.area_statistics.to_dict(),
            "mep_system_types": [item.to_dict() for item in self.mep_system_types],
            "mep_systems": [item.to_dict() for item in self.mep_systems],
            "mep_networks": [item.to_dict() for item in self.mep_networks],
            "mep_components": [item.to_dict() for item in self.mep_components],
            "mep_connectors": [item.to_dict() for item in self.mep_connectors],
            "mep_ports": [item.to_dict() for item in self.mep_ports],
            "mep_statistics": self.mep_statistics.to_dict(),
            "connector_types": [item.to_dict() for item in self.connector_types],
            "connectors": [item.to_dict() for item in self.connectors],
            "connection_rules": [item.to_dict() for item in self.connection_rules],
            "network_memberships": [item.to_dict() for item in self.network_memberships],
            "system_memberships": [item.to_dict() for item in self.system_memberships],
            "mep_coordination_rules": [item.to_dict() for item in self.mep_coordination_rules],
            "clearance_requirements": [item.to_dict() for item in self.clearance_requirements],
            "service_zones": [item.to_dict() for item in self.service_zones],
            "mep_coordination_settings": self.mep_coordination_settings.to_dict(),
            "mep_coordination_metadata": self.mep_coordination_metadata.to_dict(),
            "mep_coordination_statistics": self.mep_coordination_statistics.to_dict(),
            "validation_severities": [item.to_dict() for item in self.validation_severities],
            "validation_categories": [item.to_dict() for item in self.validation_categories],
            "validation_rules": [item.to_dict() for item in self.validation_rules],
            "validation_profiles": [item.to_dict() for item in self.validation_profiles],
            "validation_results": [item.to_dict() for item in self.validation_results],
            "validation_statistics": self.validation_statistics.to_dict(),
            "model_check_rules": [item.to_dict() for item in self.model_check_rules],
            "model_check_profiles": [item.to_dict() for item in self.model_check_profiles],
            "model_check_results": [item.to_dict() for item in self.model_check_results],
            "model_check_statistics": self.model_check_statistics.to_dict(),
            "exchange_profiles": [item.to_dict() for item in self.exchange_profiles],
            "exchange_rules": [item.to_dict() for item in self.exchange_rules],
            "exchange_statistics": self.exchange_statistics.to_dict(),
            "categories": [category.to_dict() for category in self.categories],
            "family_categories": [category.to_dict() for category in self.family_categories],
            "families": [family.to_dict() for family in self.families],
            "element_categories": [category.to_dict() for category in self.element_categories],
            "element_definitions": [definition.to_dict() for definition in self.element_definitions],
            "material_categories": [category.to_dict() for category in self.material_categories],
            "materials": [material.to_dict() for material in self.materials],
            "material_assignments": [assignment.to_dict() for assignment in self.material_assignments],
            "material_layer_sets": [layer_set.to_dict() for layer_set in self.material_layer_sets],
            "assembly_types": [assembly_type.to_dict() for assembly_type in self.assembly_types],
            "assemblies": [assembly.to_dict() for assembly in self.assemblies],
            "assembly_templates": [assembly.to_dict() for assembly in self.assembly_templates],
            "quantity_rules": [rule.to_dict() for rule in self.quantity_rules],
            "quantity_items": [item.to_dict() for item in self.quantity_items],
            "quantity_summary": self.quantity_summary.to_dict(),
            "quantity_statistics": self.quantity_statistics.to_dict(),
            "types": [item.to_dict() for item in self.types],
            "instances": [instance.to_dict() for instance in self.instances],
            "property_sets": [item.to_dict() for item in self.property_sets],
        }

    @staticmethod
    def from_dict(data):
        """Create a BIM project from persisted data."""

        data = data or {}
        project = BIMProject(
            data.get("name", "BIM Project"),
            BuildingMetadata.from_dict(data.get("metadata", {})),
            BIMSettings.from_dict(data.get("settings", {})),
        )
        project.id = data.get("id", project.id)
        project.sites = [Site.from_dict(item) for item in data.get("sites", [])]
        project.buildings = [Building.from_dict(item) for item in data.get("buildings", [])]
        project.levels = [Level.from_dict(item) for item in data.get("levels", [])]
        project.level_definitions = [
            LevelDefinition.from_dict(item)
            for item in data.get("level_definitions", [])
        ]
        project.level_groups = [
            LevelGroup.from_dict(item)
            for item in data.get("level_groups", [])
        ]
        project.grids = [GridSystem.from_dict(item) for item in data.get("grids", [])]
        project.grid_lines = [
            GridLine.from_dict(item)
            for item in data.get("grid_lines", [])
        ]
        project.grid_intersections = [
            GridIntersection.from_dict(item)
            for item in data.get("grid_intersections", [])
        ]
        project.grid_groups = [
            GridGroup.from_dict(item)
            for item in data.get("grid_groups", [])
        ]
        project.grid_statistics = GridStatistics.from_dict(data.get("grid_statistics", {}))
        project.views = [BIMView.from_dict(item) for item in data.get("views", [])]
        project.view_templates = [
            ViewTemplate.from_dict(item)
            for item in data.get("view_templates", [])
        ]
        project.view_statistics = ViewStatistics.from_dict(data.get("view_statistics", {}))
        project.sheets = [DrawingSheet.from_dict(item) for item in data.get("sheets", [])]
        project.documentation_settings = DocumentationSettings.from_dict(data.get("documentation_settings", {}))
        project.schedules = [
            ScheduleDefinition.from_dict(item)
            for item in data.get("schedules", [])
        ]
        project.schedule_templates = [
            ScheduleDefinition.from_dict(item)
            for item in data.get("schedule_templates", [])
        ]
        project.schedule_statistics = ScheduleStatistics.from_dict(data.get("schedule_statistics", {}))
        project.classification_systems = [
            ClassificationSystem.from_dict(item)
            for item in data.get("classification_systems", [])
        ]
        project.classification_mappings = [
            ClassificationMapping.from_dict(item)
            for item in data.get("classification_mappings", [])
        ]
        project.classification_statistics = ClassificationStatistics.from_dict(data.get("classification_statistics", {}))
        project.ifc_project = (
            IFCProject.from_dict(data.get("ifc_project"))
            if data.get("ifc_project") else None
        )
        project.ifc_sites = [IFCSite.from_dict(item) for item in data.get("ifc_sites", [])]
        project.ifc_buildings = [IFCBuilding.from_dict(item) for item in data.get("ifc_buildings", [])]
        project.ifc_storeys = [IFCStorey.from_dict(item) for item in data.get("ifc_storeys", [])]
        project.ifc_elements = [IFCElement.from_dict(item) for item in data.get("ifc_elements", [])]
        project.ifc_relationships = [
            IFCRelationship.from_dict(item)
            for item in data.get("ifc_relationships", [])
        ]
        project.ifc_property_sets = [
            IFCPropertySet.from_dict(item)
            for item in data.get("ifc_property_sets", [])
        ]
        project.ifc_export_settings = IFCExportSettings.from_dict(data.get("ifc_export_settings", {}))
        project.ifc_import_settings = IFCImportSettings.from_dict(data.get("ifc_import_settings", {}))
        project.ifc_metadata = IFCMetadata.from_dict(data.get("ifc_metadata", {}))
        project.relationship_types = [
            RelationshipType.from_dict(item)
            for item in data.get("relationship_types", [])
        ]
        project.relationships = [
            BIMRelationship.from_dict(item)
            for item in data.get("relationships", [])
        ]
        project.relationship_statistics = RelationshipStatistics.from_dict(data.get("relationship_statistics", {}))
        project.host_objects = [
            HostObject.from_dict(item)
            for item in data.get("host_objects", [])
        ]
        project.hosted_objects = [
            HostedObject.from_dict(item)
            for item in data.get("hosted_objects", [])
        ]
        project.openings = [
            Opening.from_dict(item)
            for item in data.get("openings", [])
        ]
        project.voids = [
            Void.from_dict(item)
            for item in data.get("voids", [])
        ]
        project.cut_relationships = [
            CutRelationship.from_dict(item)
            for item in data.get("cut_relationships", [])
        ]
        project.connection_types = [
            ConnectionType.from_dict(item)
            for item in data.get("connection_types", [])
        ]
        project.connections = [
            Connection.from_dict(item)
            for item in data.get("connections", [])
        ]
        project.connection_statistics = ConnectionStatistics.from_dict(data.get("connection_statistics", {}))
        project.design_option_sets = [
            DesignOptionSet.from_dict(item)
            for item in data.get("design_option_sets", [])
        ]
        project.design_options = [
            DesignOption.from_dict(item)
            for item in data.get("design_options", [])
        ]
        project.option_memberships = [
            OptionMembership.from_dict(item)
            for item in data.get("option_memberships", [])
        ]
        project.option_statistics = OptionStatistics.from_dict(data.get("option_statistics", {}))
        project.phases = [
            ProjectPhase.from_dict(item)
            for item in data.get("phases", [])
        ]
        project.phase_sequences = [
            PhaseSequence.from_dict(item)
            for item in data.get("phase_sequences", [])
        ]
        project.phase_filters = [
            PhaseFilter.from_dict(item)
            for item in data.get("phase_filters", [])
        ]
        project.phase_assignments = [
            PhaseAssignment.from_dict(item)
            for item in data.get("phase_assignments", [])
        ]
        project.phase_statistics = PhaseStatistics.from_dict(data.get("phase_statistics", {}))
        project.lifecycle_states = [
            LifecycleState.from_dict(item)
            for item in data.get("lifecycle_states", [])
        ]
        project.lifecycle_events = [
            LifecycleEvent.from_dict(item)
            for item in data.get("lifecycle_events", [])
        ]
        project.lifecycle_statistics = LifecycleStatistics.from_dict(data.get("lifecycle_statistics", {}))
        project.rooms = [
            Room.from_dict(item)
            for item in data.get("rooms", [])
        ]
        project.room_boundaries = [
            RoomBoundary.from_dict(item)
            for item in data.get("room_boundaries", [])
        ]
        project.room_statistics = RoomStatistics.from_dict(data.get("room_statistics", {}))
        project.spaces = [
            Space.from_dict(item)
            for item in data.get("spaces", [])
        ]
        project.space_boundaries = [
            SpaceBoundary.from_dict(item)
            for item in data.get("space_boundaries", [])
        ]
        project.space_statistics = SpaceStatistics.from_dict(data.get("space_statistics", {}))
        project.zones = [
            Zone.from_dict(item)
            for item in data.get("zones", [])
        ]
        project.zone_groups = [
            ZoneGroup.from_dict(item)
            for item in data.get("zone_groups", [])
        ]
        project.zone_statistics = ZoneStatistics.from_dict(data.get("zone_statistics", {}))
        project.area_regions = [
            AreaRegion.from_dict(item)
            for item in data.get("area_regions", [])
        ]
        project.area_boundaries = [
            AreaBoundary.from_dict(item)
            for item in data.get("area_boundaries", [])
        ]
        project.area_summary = AreaSummary.from_dict(data.get("area_summary", {}))
        project.area_statistics = AreaStatistics.from_dict(data.get("area_statistics", {}))
        project.mep_system_types = [
            MEPSystemType.from_dict(item)
            for item in data.get("mep_system_types", [])
        ]
        project.mep_systems = [
            MEPSystem.from_dict(item)
            for item in data.get("mep_systems", [])
        ]
        project.mep_networks = [
            MEPNetwork.from_dict(item)
            for item in data.get("mep_networks", [])
        ]
        project.mep_components = [
            MEPComponent.from_dict(item)
            for item in data.get("mep_components", [])
        ]
        project.mep_connectors = [
            MEPConnector.from_dict(item)
            for item in data.get("mep_connectors", [])
        ]
        project.mep_ports = [
            MEPPort.from_dict(item)
            for item in data.get("mep_ports", [])
        ]
        project.mep_statistics = MEPStatistics.from_dict(data.get("mep_statistics", {}))
        project.connector_types = [
            ConnectorType.from_dict(item)
            for item in data.get("connector_types", [])
        ]
        project.connectors = [
            Connector.from_dict(item)
            for item in data.get("connectors", [])
        ]
        project.connection_rules = [
            ConnectionRule.from_dict(item)
            for item in data.get("connection_rules", [])
        ]
        project.network_memberships = [
            NetworkMembership.from_dict(item)
            for item in data.get("network_memberships", [])
        ]
        project.system_memberships = [
            SystemMembership.from_dict(item)
            for item in data.get("system_memberships", [])
        ]
        project.mep_coordination_rules = [
            CoordinationRule.from_dict(item)
            for item in data.get("mep_coordination_rules", [])
        ]
        project.clearance_requirements = [
            ClearanceRequirement.from_dict(item)
            for item in data.get("clearance_requirements", [])
        ]
        project.service_zones = [
            ServiceZone.from_dict(item)
            for item in data.get("service_zones", [])
        ]
        project.mep_coordination_settings = MEPCoordinationSettings.from_dict(data.get("mep_coordination_settings", {}))
        project.mep_coordination_metadata = MEPCoordinationMetadata.from_dict(data.get("mep_coordination_metadata", {}))
        project.mep_coordination_statistics = MEPCoordinationStatistics.from_dict(data.get("mep_coordination_statistics", {}))
        project.validation_severities = [
            ValidationSeverity.from_dict(item)
            for item in data.get("validation_severities", [])
        ]
        project.validation_categories = [
            ValidationCategory.from_dict(item)
            for item in data.get("validation_categories", [])
        ]
        project.validation_rules = [
            ValidationRule.from_dict(item)
            for item in data.get("validation_rules", [])
        ]
        project.validation_profiles = [
            ValidationProfile.from_dict(item)
            for item in data.get("validation_profiles", [])
        ]
        project.validation_results = [
            ValidationResult.from_dict(item)
            for item in data.get("validation_results", [])
        ]
        project.validation_statistics = ValidationStatistics.from_dict(data.get("validation_statistics", {}))
        project.model_check_rules = [
            ModelCheckRule.from_dict(item)
            for item in data.get("model_check_rules", [])
        ]
        project.model_check_profiles = [
            ModelCheckProfile.from_dict(item)
            for item in data.get("model_check_profiles", [])
        ]
        project.model_check_results = [
            ModelCheckResult.from_dict(item)
            for item in data.get("model_check_results", [])
        ]
        project.model_check_statistics = ModelCheckStatistics.from_dict(data.get("model_check_statistics", {}))
        project.exchange_profiles = [
            ExchangeProfile.from_dict(item)
            for item in data.get("exchange_profiles", [])
        ]
        project.exchange_rules = [
            ExchangeRule.from_dict(item)
            for item in data.get("exchange_rules", [])
        ]
        project.exchange_statistics = ExchangeStatistics.from_dict(data.get("exchange_statistics", {}))
        project.categories = [BIMCategory.from_dict(item) for item in data.get("categories", [])]
        project.family_categories = [
            FamilyCategory.from_dict(item)
            for item in data.get("family_categories", [])
        ]
        project.families = [BIMFamily.from_dict(item) for item in data.get("families", [])]
        project.element_categories = [
            ElementCategoryMetadata.from_dict(item)
            for item in data.get("element_categories", [])
        ]
        project.element_definitions = [
            BIMElementDefinition.from_dict(item)
            for item in data.get("element_definitions", [])
        ]
        project.material_categories = [
            MaterialCategory.from_dict(item)
            for item in data.get("material_categories", [])
        ]
        project.materials = [BIMMaterial.from_dict(item) for item in data.get("materials", [])]
        project.material_assignments = [
            MaterialAssignment.from_dict(item)
            for item in data.get("material_assignments", [])
        ]
        project.material_layer_sets = [
            MaterialLayerSet.from_dict(item)
            for item in data.get("material_layer_sets", [])
        ]
        project.assembly_types = [
            AssemblyType.from_dict(item)
            for item in data.get("assembly_types", [])
        ]
        project.assemblies = [Assembly.from_dict(item) for item in data.get("assemblies", [])]
        project.assembly_templates = [
            Assembly.from_dict(item)
            for item in data.get("assembly_templates", [])
        ]
        project.quantity_rules = [
            QuantityRule.from_dict(item)
            for item in data.get("quantity_rules", [])
        ]
        project.quantity_items = [
            QuantityItem.from_dict(item)
            for item in data.get("quantity_items", [])
        ]
        project.quantity_summary = QuantitySummary.from_dict(data.get("quantity_summary", {}))
        project.quantity_statistics = QuantityStatistics.from_dict(data.get("quantity_statistics", {}))
        project.types = [BIMType.from_dict(item) for item in data.get("types", [])]
        project.instances = [BIMInstance.from_dict(item) for item in data.get("instances", [])]
        project.property_sets = [
            PropertySet.from_dict(item)
            for item in data.get("property_sets", [])
        ]

        return project


class BIMManager:
    """Workspace-owned BIM project, hierarchy and object metadata manager."""

    def __init__(self):

        self.projects = []
        self.active_project_id = None
        self.visible = True
        self.browser_state = {}

    @property
    def active_project(self):
        """Return the active BIM project."""

        if not self.projects:
            return None

        return self.get_project(self.active_project_id) or self.projects[-1]

    def create_project(self, name="BIM Project", metadata=None, settings=None):
        """Create and store a BIM project."""

        project = BIMProject(name, metadata, settings)
        self.add_project(project)

        return project

    def add_project(self, project):
        """Store a BIM project."""

        if project not in self.projects:
            self.projects.append(project)

        self.active_project_id = project.id

        return project

    def remove_project(self, project):
        """Remove a BIM project."""

        target = self.get_project(project)

        if target is None:
            return False

        self.projects.remove(target)
        if self.active_project_id == target.id:
            self.active_project_id = self.projects[-1].id if self.projects else None

        return True

    def get_project(self, project):
        """Return a BIM project by object, id or name."""

        if isinstance(project, BIMProject):
            return project if project in self.projects else None

        for item in self.projects:
            if item.id == project or item.name == project:
                return item

        return None

    def ensure_project(self):
        """Return an active project, creating a default when needed."""

        return self.active_project or self.create_project()

    def add_site(self, site):
        """Add a site to the active BIM project."""

        project = self.ensure_project()

        if site not in project.sites:
            project.sites.append(site)

        return site

    def add_building(self, building):
        """Add a building to the active BIM project."""

        project = self.ensure_project()

        if building not in project.buildings:
            project.buildings.append(building)

        return building

    def add_level(self, level):
        """Add a level to the active BIM project."""

        project = self.ensure_project()

        if level not in project.levels:
            project.levels.append(level)

        return level

    @property
    def level_manager(self):
        """Return the active project's professional level helper."""

        return LevelManager(self.ensure_project())

    def add_level_definition(self, definition):
        """Add a professional level definition."""

        return self.level_manager.add_definition(definition)

    def add_level_group(self, group):
        """Add a professional level group."""

        return self.level_manager.add_group(group)

    def add_grid(self, grid):
        """Add a grid system to the active BIM project."""

        project = self.ensure_project()

        if grid not in project.grids:
            project.grids.append(grid)

        return grid

    @property
    def grid_manager(self):
        """Return the active project's professional grid helper."""

        return GridManager(self.ensure_project())

    def add_grid_line(self, line):
        """Add a professional grid line."""

        return self.grid_manager.add_line(line)

    def add_grid_intersection(self, intersection):
        """Add a professional grid intersection."""

        return self.grid_manager.add_intersection(intersection)

    def add_grid_group(self, group):
        """Add a professional grid group."""

        return self.grid_manager.add_group(group)

    @property
    def view_manager(self):
        """Return the active project's BIM view helper."""

        return ViewManager(self.ensure_project())

    def add_view(self, view):
        """Add a BIM documentation view."""

        return self.view_manager.add_view(view)

    def add_view_template(self, template):
        """Add a BIM view template."""

        return self.view_manager.add_template(template)

    @property
    def sheet_manager(self):
        """Return the active project's sheet helper."""

        return SheetManager(self.ensure_project())

    def add_sheet(self, sheet):
        """Add a BIM drawing sheet."""

        return self.sheet_manager.add_sheet(sheet)

    @property
    def schedule_manager(self):
        """Return the active project's schedule helper."""

        return ScheduleManager(self.ensure_project())

    def add_schedule(self, schedule):
        """Add a BIM schedule definition."""

        return self.schedule_manager.add_schedule(schedule)

    def build_schedule(self, schedule):
        """Build a BIM schedule from existing BIM data."""

        return self.schedule_manager.build_schedule(schedule)

    @property
    def classification_manager(self):
        """Return the active project's classification helper."""

        return ClassificationManager(self.ensure_project())

    def add_classification_system(self, system):
        """Add a BIM classification system."""

        return self.classification_manager.add_system(system)

    def add_classification_mapping(self, mapping):
        """Add a BIM classification mapping."""

        return self.classification_manager.add_mapping(mapping)

    @property
    def ifc_manager(self):
        """Return the active project's IFC metadata helper."""

        return IFCManager(self.ensure_project())

    def add_ifc_item(self, item):
        """Add IFC foundation metadata."""

        return self.ifc_manager.add_item(item)

    @property
    def relationship_manager(self):
        """Return the active project's relationship graph helper."""

        return RelationshipManager(self.ensure_project())

    def add_relationship_item(self, item):
        """Add relationship graph metadata."""

        if isinstance(item, RelationshipType):
            return self.relationship_manager.add_type(item)
        if isinstance(item, BIMRelationship):
            return self.relationship_manager.add_relationship(item)

        project = self.ensure_project()

        if isinstance(item, HostObject):
            if item not in project.host_objects:
                project.host_objects.append(item)
            self.relationship_manager.statistics()
            return item
        if isinstance(item, HostedObject):
            if item not in project.hosted_objects:
                project.hosted_objects.append(item)
            self.relationship_manager.statistics()
            return item
        if isinstance(item, Opening):
            collection = project.voids if isinstance(item, Void) else project.openings
            if item not in collection:
                collection.append(item)
            self.relationship_manager.statistics()
            return item
        if isinstance(item, CutRelationship):
            if item not in project.cut_relationships:
                project.cut_relationships.append(item)
            self.relationship_manager.statistics()
            return item

        return None

    @property
    def connectivity_manager(self):
        """Return the active project's connectivity graph helper."""

        return ConnectivityManager(self.ensure_project())

    def add_connection_item(self, item):
        """Add connectivity metadata."""

        if isinstance(item, ConnectionType):
            return self.connectivity_manager.add_type(item)
        if isinstance(item, Connection):
            return self.connectivity_manager.add_connection(item)

        return None

    @property
    def design_option_manager(self):
        """Return the active project's design option helper."""

        return DesignOptionManager(self.ensure_project())

    def add_design_option_item(self, item):
        """Add design option metadata."""

        if isinstance(item, DesignOptionSet):
            return self.design_option_manager.add_set(item)
        if isinstance(item, DesignOption):
            return self.design_option_manager.add_option(item)
        if isinstance(item, OptionMembership):
            return self.design_option_manager.add_membership(item)

        return None

    @property
    def phase_manager(self):
        """Return the active project's phase helper."""

        return PhaseManager(self.ensure_project())

    def add_phase_item(self, item):
        """Add project phasing metadata."""

        if isinstance(item, ProjectPhase):
            return self.phase_manager.add_phase(item)
        if isinstance(item, PhaseSequence):
            return self.phase_manager.add_sequence(item)
        if isinstance(item, PhaseFilter):
            return self.phase_manager.add_filter(item)
        if isinstance(item, PhaseAssignment):
            return self.phase_manager.add_assignment(item)

        return None

    @property
    def lifecycle_manager(self):
        """Return the active project's lifecycle helper."""

        return LifecycleManager(self.ensure_project())

    def add_lifecycle_item(self, item):
        """Add lifecycle metadata."""

        if isinstance(item, LifecycleState):
            return self.lifecycle_manager.add_state(item)
        if isinstance(item, LifecycleEvent):
            return self.lifecycle_manager.add_event(item)

        return None

    @property
    def room_manager(self):
        """Return the active project's room helper."""

        return RoomManager(self.ensure_project())

    def add_room_item(self, item):
        """Add room metadata."""

        if isinstance(item, Room):
            return self.room_manager.add_room(item)
        if isinstance(item, RoomBoundary):
            return self.room_manager.add_boundary(item)

        return None

    @property
    def space_manager(self):
        """Return the active project's space helper."""

        return SpaceManager(self.ensure_project())

    def add_space_item(self, item):
        """Add space metadata."""

        if isinstance(item, Space):
            return self.space_manager.add_space(item)
        if isinstance(item, SpaceBoundary):
            return self.space_manager.add_boundary(item)

        return None

    @property
    def zone_manager(self):
        """Return the active project's zone helper."""

        return ZoneManager(self.ensure_project())

    def add_zone_item(self, item):
        """Add zone metadata."""

        if isinstance(item, Zone):
            return self.zone_manager.add_zone(item)
        if isinstance(item, ZoneGroup):
            return self.zone_manager.add_group(item)

        return None

    @property
    def area_analysis_manager(self):
        """Return the active project's area analysis helper."""

        return AreaAnalysisManager(self.ensure_project())

    def add_area_item(self, item):
        """Add area analysis metadata."""

        if isinstance(item, AreaRegion):
            return self.area_analysis_manager.add_region(item)
        if isinstance(item, AreaBoundary):
            return self.area_analysis_manager.add_boundary(item)

        return None

    @property
    def mep_manager(self):
        """Return the active project's MEP foundation helper."""

        return MEPManager(self.ensure_project())

    def add_mep_item(self, item):
        """Add MEP foundation metadata."""

        return self.mep_manager.add_item(item)

    @property
    def connector_manager(self):
        """Return the active project's connector helper."""

        return ConnectorManager(self.ensure_project())

    def add_connector_item(self, item):
        """Add connector topology metadata."""

        return self.connector_manager.add_item(item)

    @property
    def validation_manager(self):
        """Return the active project's BIM validation helper."""

        return ValidationManager(self.ensure_project())

    def add_validation_item(self, item):
        """Add BIM validation metadata."""

        return self.validation_manager.add_item(item)

    @property
    def model_check_manager(self):
        """Return the active project's model checking helper."""

        return ModelCheckManager(self.ensure_project())

    def add_model_check_item(self, item):
        """Add BIM model checking metadata."""

        return self.model_check_manager.add_item(item)

    @property
    def interoperability_manager(self):
        """Return the active project's interoperability helper."""

        return InteroperabilityManager(self.ensure_project())

    def add_interoperability_item(self, item):
        """Add BIM interoperability metadata."""

        return self.interoperability_manager.add_item(item)

    def add_category(self, category):
        """Add a category to the active BIM project."""

        project = self.ensure_project()

        if category not in project.categories:
            project.categories.append(category)

        return category

    def add_family_category(self, category):
        """Add a family category to the active BIM project."""

        project = self.ensure_project()

        if category not in project.family_categories:
            project.family_categories.append(category)

        return category

    @property
    def family_library(self):
        """Return the active project's family library helper."""

        return BIMFamilyLibrary(self.ensure_project())

    def add_family(self, family):
        """Add a BIM family to the active project."""

        return self.family_library.add_family(family)

    def remove_family(self, family):
        """Remove a BIM family from the active project."""

        return self.family_library.remove_family(family)

    @property
    def element_library(self):
        """Return the active project's element library helper."""

        return BIMElementLibrary(self.ensure_project())

    def add_element_category(self, category):
        """Add an element category to the active BIM project."""

        project = self.ensure_project()

        if category not in project.element_categories:
            project.element_categories.append(category)

        return category

    def add_element_definition(self, definition):
        """Add a professional BIM element definition."""

        return self.element_library.add_definition(definition)

    def remove_element_definition(self, definition):
        """Remove a professional BIM element definition."""

        return self.element_library.remove_definition(definition)

    @property
    def material_library(self):
        """Return the active project's material library helper."""

        return MaterialLibrary(self.ensure_project())

    @property
    def quantity_manager(self):
        """Return the active project's quantity takeoff helper."""

        return QuantityManager(self.ensure_project())

    def add_material_category(self, category):
        """Add a material category to the active BIM project."""

        project = self.ensure_project()

        if category not in project.material_categories:
            project.material_categories.append(category)

        return category

    def add_material(self, material):
        """Add a material to the active BIM project."""

        return self.material_library.add_material(material)

    def add_material_assignment(self, assignment):
        """Assign material metadata to an existing BIM item."""

        project = self.ensure_project()

        if assignment not in project.material_assignments:
            project.material_assignments.append(assignment)

        target = self.get_object(assignment.target_id)
        if target is not None:
            target.material_assignment_id = assignment.id

        return assignment

    def add_material_layer_set(self, layer_set):
        """Add a material layer set to the active BIM project."""

        project = self.ensure_project()

        if layer_set not in project.material_layer_sets:
            project.material_layer_sets.append(layer_set)

        return layer_set

    def add_assembly_type(self, assembly_type):
        """Add an assembly type or template definition."""

        project = self.ensure_project()

        if assembly_type not in project.assembly_types:
            project.assembly_types.append(assembly_type)

        return assembly_type

    def add_assembly(self, assembly, template=False):
        """Add an assembly that references existing BIM instances."""

        project = self.ensure_project()
        collection = project.assembly_templates if template else project.assemblies

        if assembly not in collection:
            collection.append(assembly)

        for member in assembly.members:
            target = self.get_object(member.reference_id)

            if target is not None:
                assembly_ids = getattr(target, "assembly_ids", [])
                if assembly.id not in assembly_ids:
                    assembly_ids.append(assembly.id)
                target.assembly_ids = assembly_ids

        assembly.refresh_statistics()

        return assembly

    def add_quantity_rule(self, rule):
        """Add a quantity takeoff rule."""

        project = self.ensure_project()

        if rule not in project.quantity_rules:
            project.quantity_rules.append(rule)

        return rule

    def run_quantity_takeoff(self):
        """Run quantity aggregation using existing BIM data."""

        return self.quantity_manager.run()

    def add_type(self, item):
        """Add a BIM type to the active project."""

        project = self.ensure_project()

        if item not in project.types:
            project.types.append(item)

        family = self.family_library.get_family(getattr(item, "family_id", ""))
        if family is not None and item.id not in family.type_ids:
            family.type_ids.append(item.id)
            family.refresh_statistics(project)

        element = self.element_library.get_definition(getattr(item, "element_definition_id", ""))
        if element is not None and item.id not in element.type_ids:
            element.type_ids.append(item.id)

        return item

    def add_instance(self, instance):
        """Add a BIM object instance to the active project."""

        project = self.ensure_project()

        if instance not in project.instances:
            project.instances.append(instance)

        family = self.family_library.get_family(getattr(instance, "family_id", ""))
        if family is not None:
            family.refresh_statistics(project)

        return instance

    def add_property_set(self, property_set):
        """Add a property set to the active BIM project."""

        project = self.ensure_project()

        if property_set not in project.property_sets:
            project.property_sets.append(property_set)

        owner = self.get_object(property_set.owner_id)

        if owner is not None and hasattr(owner, "property_set_ids"):
            if property_set.id not in owner.property_set_ids:
                owner.property_set_ids.append(property_set.id)
            if hasattr(owner, "property_sets"):
                owner.property_sets[property_set.name] = {
                    definition.name: value.value
                    for definition in property_set.definitions
                    for value in property_set.values
                    if value.definition_id == definition.id
                }

        family = self.family_library.get_family(property_set.owner_id)
        if family is not None:
            if property_set.id not in family.default_property_set_ids:
                family.default_property_set_ids.append(property_set.id)
            family.refresh_statistics(project)

        return property_set

    def add_object(self, item):
        """Add any supported BIM hierarchy or object item."""

        if isinstance(item, Site):
            return self.add_site(item)
        if isinstance(item, Building):
            return self.add_building(item)
        if isinstance(item, Level):
            return self.add_level(item)
        if isinstance(item, LevelDefinition):
            return self.add_level_definition(item)
        if isinstance(item, LevelGroup):
            return self.add_level_group(item)
        if isinstance(item, GridSystem):
            return self.add_grid(item)
        if isinstance(item, GridLine):
            return self.add_grid_line(item)
        if isinstance(item, GridIntersection):
            return self.add_grid_intersection(item)
        if isinstance(item, GridGroup):
            return self.add_grid_group(item)
        if isinstance(item, BIMView):
            return self.add_view(item)
        if isinstance(item, ViewTemplate):
            return self.add_view_template(item)
        if isinstance(item, DrawingSheet):
            return self.add_sheet(item)
        if isinstance(item, ScheduleDefinition):
            return self.add_schedule(item)
        if isinstance(item, ClassificationSystem):
            return self.add_classification_system(item)
        if isinstance(item, ClassificationMapping):
            return self.add_classification_mapping(item)
        if isinstance(item, (IFCProject, IFCSite, IFCBuilding, IFCStorey, IFCElement, IFCRelationship, IFCPropertySet)):
            return self.add_ifc_item(item)
        if isinstance(item, (RelationshipType, BIMRelationship, HostObject, HostedObject, Opening, CutRelationship)):
            return self.add_relationship_item(item)
        if isinstance(item, (ConnectionType, Connection)):
            return self.add_connection_item(item)
        if isinstance(item, (DesignOptionSet, DesignOption, OptionMembership)):
            return self.add_design_option_item(item)
        if isinstance(item, (ProjectPhase, PhaseSequence, PhaseFilter, PhaseAssignment)):
            return self.add_phase_item(item)
        if isinstance(item, (LifecycleState, LifecycleEvent)):
            return self.add_lifecycle_item(item)
        if isinstance(item, (Room, RoomBoundary)):
            return self.add_room_item(item)
        if isinstance(item, (Space, SpaceBoundary)):
            return self.add_space_item(item)
        if isinstance(item, (Zone, ZoneGroup)):
            return self.add_zone_item(item)
        if isinstance(item, (AreaRegion, AreaBoundary)):
            return self.add_area_item(item)
        if isinstance(item, (MEPSystemType, MEPSystem, MEPNetwork, MEPComponent, MEPConnector, MEPPort, CoordinationRule, ClearanceRequirement, ServiceZone)):
            return self.add_mep_item(item)
        if isinstance(item, (ConnectorType, Connector, ConnectionRule, NetworkMembership, SystemMembership)):
            return self.add_connector_item(item)
        if isinstance(item, (ValidationSeverity, ValidationCategory, ValidationRule, ValidationResult, ValidationProfile)):
            return self.add_validation_item(item)
        if isinstance(item, (ModelCheckRule, ModelCheckResult, ModelCheckProfile)):
            return self.add_model_check_item(item)
        if isinstance(item, (ExchangeRule, ExchangeProfile)):
            return self.add_interoperability_item(item)
        if isinstance(item, BIMCategory):
            return self.add_category(item)
        if isinstance(item, FamilyCategory):
            return self.add_family_category(item)
        if isinstance(item, BIMFamily):
            return self.add_family(item)
        if isinstance(item, ElementCategoryMetadata):
            return self.add_element_category(item)
        if isinstance(item, BIMElementDefinition):
            return self.add_element_definition(item)
        if isinstance(item, MaterialCategory):
            return self.add_material_category(item)
        if isinstance(item, BIMMaterial):
            return self.add_material(item)
        if isinstance(item, MaterialAssignment):
            return self.add_material_assignment(item)
        if isinstance(item, MaterialLayerSet):
            return self.add_material_layer_set(item)
        if isinstance(item, AssemblyType):
            return self.add_assembly_type(item)
        if isinstance(item, Assembly):
            return self.add_assembly(item)
        if isinstance(item, QuantityRule):
            return self.add_quantity_rule(item)
        if isinstance(item, PropertySet):
            return self.add_property_set(item)
        if isinstance(item, BIMType):
            return self.add_type(item)
        if isinstance(item, BIMObject):
            return self.add_instance(item)

        return None

    def remove_object(self, item):
        """Remove a BIM hierarchy or object item."""

        project = self.active_project

        if project is None:
            return False

        collections = (
            project.sites,
            project.buildings,
            project.levels,
            project.level_definitions,
            project.level_groups,
            project.grids,
            project.grid_lines,
            project.grid_intersections,
            project.grid_groups,
            project.views,
            project.view_templates,
            project.sheets,
            project.schedules,
            project.schedule_templates,
            project.classification_systems,
            project.classification_mappings,
            project.ifc_sites,
            project.ifc_buildings,
            project.ifc_storeys,
            project.ifc_elements,
            project.ifc_relationships,
            project.ifc_property_sets,
            project.relationship_types,
            project.relationships,
            project.host_objects,
            project.hosted_objects,
            project.openings,
            project.voids,
            project.cut_relationships,
            project.connection_types,
            project.connections,
            project.design_option_sets,
            project.design_options,
            project.option_memberships,
            project.phases,
            project.phase_sequences,
            project.phase_filters,
            project.phase_assignments,
            project.lifecycle_states,
            project.lifecycle_events,
            project.rooms,
            project.room_boundaries,
            project.spaces,
            project.space_boundaries,
            project.zones,
            project.zone_groups,
            project.area_regions,
            project.area_boundaries,
            project.mep_system_types,
            project.mep_systems,
            project.mep_networks,
            project.mep_components,
            project.mep_connectors,
            project.mep_ports,
            project.connector_types,
            project.connectors,
            project.connection_rules,
            project.network_memberships,
            project.system_memberships,
            project.mep_coordination_rules,
            project.clearance_requirements,
            project.service_zones,
            project.validation_severities,
            project.validation_categories,
            project.validation_rules,
            project.validation_profiles,
            project.validation_results,
            project.model_check_rules,
            project.model_check_profiles,
            project.model_check_results,
            project.exchange_profiles,
            project.exchange_rules,
            project.categories,
            project.family_categories,
            project.families,
            project.element_categories,
            project.element_definitions,
            project.material_categories,
            project.materials,
            project.material_assignments,
            project.material_layer_sets,
            project.assembly_types,
            project.assemblies,
            project.assembly_templates,
            project.quantity_rules,
            project.quantity_items,
            project.types,
            project.instances,
            project.property_sets,
        )

        for collection in collections:
            if item in collection:
                collection.remove(item)
                if isinstance(item, MaterialAssignment):
                    target = self.get_object(item.target_id)
                    if target is not None and getattr(target, "material_assignment_id", "") == item.id:
                        target.material_assignment_id = ""
                if isinstance(item, Assembly):
                    for member in item.members:
                        target = self.get_object(member.reference_id)
                        if target is not None and item.id in getattr(target, "assembly_ids", []):
                            target.assembly_ids.remove(item.id)
                return True

        if isinstance(item, IFCProject) and project.ifc_project is item:
            project.ifc_project = None
            return True

        return False

    def visible_levels(self):
        """Return visible level markers."""

        if not self.visible:
            return []

        return list(_visible_items(self.active_project, "levels"))

    def visible_grids(self):
        """Return visible grid system markers."""

        if not self.visible:
            return []

        return list(_visible_items(self.active_project, "grids"))

    def visible_grid_lines(self):
        """Return visible professional grid lines."""

        if not self.visible:
            return []

        return list(_visible_items(self.active_project, "grid_lines"))

    def visible_grid_intersections(self):
        """Return visible professional grid intersections."""

        if not self.visible:
            return []

        return list(_visible_items(self.active_project, "grid_intersections"))

    def visible_views(self):
        """Return visible BIM documentation views."""

        if not self.visible:
            return []

        return list(_visible_items(self.active_project, "views"))

    def visible_sheets(self):
        """Return visible BIM drawing sheets."""

        if not self.visible:
            return []

        return list(_visible_items(self.active_project, "sheets"))

    def visible_instances(self):
        """Return visible BIM object instances."""

        if not self.visible:
            return []

        return list(_visible_items(self.active_project, "instances"))

    def visible_objects(self):
        """Return all visible renderable/selectable BIM items."""

        return (
            self.visible_levels() +
            self.visible_grids() +
            self.visible_grid_lines() +
            self.visible_grid_intersections() +
            self.visible_views() +
            self.visible_sheets() +
            self.visible_instances()
        )

    def get_object(self, identifier):
        """Return any BIM family, type, instance or property item by id or name."""

        project = self.active_project

        if project is None:
            return None

        for collection in (
            project.family_categories,
            project.families,
            project.element_definitions,
            project.level_definitions,
            project.level_groups,
            project.grid_lines,
            project.grid_intersections,
            project.grid_groups,
            project.views,
            project.view_templates,
            project.sheets,
            project.schedules,
            project.schedule_templates,
            project.classification_systems,
            project.classification_mappings,
            project.ifc_sites,
            project.ifc_buildings,
            project.ifc_storeys,
            project.ifc_elements,
            project.ifc_relationships,
            project.ifc_property_sets,
            project.relationship_types,
            project.relationships,
            project.host_objects,
            project.hosted_objects,
            project.openings,
            project.voids,
            project.cut_relationships,
            project.connection_types,
            project.connections,
            project.design_option_sets,
            project.design_options,
            project.option_memberships,
            project.phases,
            project.phase_sequences,
            project.phase_filters,
            project.phase_assignments,
            project.lifecycle_states,
            project.lifecycle_events,
            project.rooms,
            project.room_boundaries,
            project.spaces,
            project.space_boundaries,
            project.zones,
            project.zone_groups,
            project.area_regions,
            project.area_boundaries,
            project.mep_system_types,
            project.mep_systems,
            project.mep_networks,
            project.mep_components,
            project.mep_connectors,
            project.mep_ports,
            project.connector_types,
            project.connectors,
            project.connection_rules,
            project.network_memberships,
            project.system_memberships,
            project.mep_coordination_rules,
            project.clearance_requirements,
            project.service_zones,
            project.validation_severities,
            project.validation_categories,
            project.validation_rules,
            project.validation_profiles,
            project.validation_results,
            project.model_check_rules,
            project.model_check_profiles,
            project.model_check_results,
            project.exchange_profiles,
            project.exchange_rules,
            project.material_categories,
            project.materials,
            project.material_assignments,
            project.material_layer_sets,
            project.assembly_types,
            project.assemblies,
            project.assembly_templates,
            project.quantity_rules,
            project.quantity_items,
            project.types,
            project.instances,
            project.property_sets,
            project.categories,
        ):
            for item in collection:
                if item is identifier:
                    return item
                if getattr(item, "id", None) == identifier or getattr(item, "name", None) == identifier:
                    return item

        return None

    def material_for(self, item):
        """Return the material assigned to a BIM instance, type, family or assembly."""

        project = self.active_project

        if project is None:
            return None

        item_id = getattr(item, "id", item)
        assignment = next(
            (
                value for value in project.material_assignments
                if value.target_id == item_id or value.id == getattr(item, "material_assignment_id", "")
            ),
            None,
        )

        if assignment is None:
            return None

        return self.material_library.get_material(assignment.material_id)

    def assemblies_for(self, item):
        """Return assemblies containing a BIM instance or nested assembly."""

        project = self.active_project

        if project is None:
            return []

        item_id = getattr(item, "id", item)

        return [
            assembly for assembly in project.assemblies + project.assembly_templates
            if item_id in [member.reference_id for member in assembly.members]
        ]

    def schedules_for(self, item):
        """Return schedules containing rows for a BIM item."""

        project = self.active_project

        if project is None:
            return []

        return ScheduleManager(project).schedules_for(item)

    def classifications_for(self, item):
        """Return classifications assigned to a BIM item."""

        project = self.active_project

        if project is None:
            return []

        return ClassificationManager(project).mappings_for(item)

    def ifc_status_for(self, item):
        """Return IFC mapping status for a BIM item."""

        project = self.active_project

        if project is None:
            return "Unmapped"

        return IFCManager(project).status_for(item)

    def relationships_for(self, item, relationship_type=None):
        """Return relationship edges connected to a BIM item."""

        project = self.active_project

        if project is None:
            return []

        return RelationshipManager(project).relationships_for(item, relationship_type)

    def hosted_objects_for(self, host):
        """Return BIM instances hosted by a host object."""

        project = self.active_project

        if project is None:
            return []

        host_id = getattr(host, "id", host)
        hosted_ids = set()

        for host_object in project.host_objects:
            if host_object.host_id == host_id:
                hosted_ids.update(host_object.hosted_ids)

        hosted_ids.update(
            item.hosted_id for item in project.hosted_objects
            if item.host_id == host_id
        )

        return [
            instance for instance in project.instances
            if instance.id in hosted_ids
        ]

    def host_for(self, hosted):
        """Return the host instance for a hosted object."""

        project = self.active_project

        if project is None:
            return None

        hosted_id = getattr(hosted, "id", hosted)
        host_link = next(
            (item for item in project.hosted_objects if item.hosted_id == hosted_id),
            None,
        )

        return _find_by_id(project.instances, getattr(host_link, "host_id", ""))

    def openings_for(self, host):
        """Return openings or voids assigned to a host."""

        project = self.active_project

        if project is None:
            return []

        host_id = getattr(host, "id", host)

        return [
            item for item in project.openings + project.voids
            if item.host_id == host_id
        ]

    def cut_relationships_for(self, host):
        """Return cut relationships assigned to a host."""

        project = self.active_project

        if project is None:
            return []

        host_id = getattr(host, "id", host)

        return [
            item for item in project.cut_relationships
            if item.host_id == host_id
        ]

    def connections_for(self, item):
        """Return connectivity edges touching a BIM item."""

        project = self.active_project

        if project is None:
            return []

        return ConnectivityManager(project).connections_for(item)

    def connected_items(self, item):
        """Return BIM instances connected to a BIM item."""

        project = self.active_project

        if project is None:
            return []

        return ConnectivityManager(project).connected_items(item)

    def design_options_for(self, item):
        """Return design option memberships for a BIM item."""

        project = self.active_project

        if project is None:
            return []

        return DesignOptionManager(project).memberships_for(item)

    def active_design_options(self):
        """Return active design options."""

        project = self.active_project

        if project is None:
            return []

        return DesignOptionManager(project).active_options()

    def phase_assignment_for(self, item):
        """Return phase assignment for a BIM item."""

        project = self.active_project

        if project is None:
            return None

        return PhaseManager(project).assignment_for(item)

    def lifecycle_events_for(self, item):
        """Return lifecycle events for a BIM item."""

        project = self.active_project

        if project is None:
            return []

        return LifecycleManager(project).events_for(item)

    def lifecycle_state_for(self, item):
        """Return current lifecycle state for a BIM item."""

        project = self.active_project

        if project is None:
            return None

        return LifecycleManager(project).current_state_for(item)

    def rooms_for(self, item):
        """Return rooms linked to a BIM element."""

        project = self.active_project

        if project is None:
            return []

        return RoomManager(project).rooms_for_element(item)

    def spaces_for(self, item):
        """Return spaces linked to a BIM element or room."""

        project = self.active_project

        if project is None:
            return []

        if isinstance(item, Room):
            return SpaceManager(project).spaces_for_room(item)

        return SpaceManager(project).spaces_for_element(item)

    def zones_for(self, item):
        """Return zones linked to a room or space."""

        project = self.active_project

        if project is None:
            return []

        if isinstance(item, Room):
            return ZoneManager(project).zones_for_room(item)
        if isinstance(item, Space):
            return ZoneManager(project).zones_for_space(item)

        rooms = self.rooms_for(item)
        spaces = self.spaces_for(item)
        zones = []
        for room in rooms:
            zones.extend(ZoneManager(project).zones_for_room(room))
        for space in spaces:
            zones.extend(ZoneManager(project).zones_for_space(space))

        unique = []
        seen = set()

        for zone in zones:
            if zone.id not in seen:
                unique.append(zone)
                seen.add(zone.id)

        return unique

    def area_regions_for(self, item):
        """Return area regions linked to a BIM element, room or space."""

        project = self.active_project

        if project is None:
            return []

        room_ids = [room.id for room in (self.rooms_for(item) if not isinstance(item, Room) else [item])]
        space_ids = [space.id for space in (self.spaces_for(item) if not isinstance(item, Space) else [item])]

        return [
            region for region in project.area_regions
            if set(room_ids).intersection(region.room_ids) or set(space_ids).intersection(region.space_ids)
        ]

    def mep_components_for(self, item):
        """Return MEP components linked to a BIM item."""

        project = self.active_project

        if project is None:
            return []

        return MEPManager(project).components_for(item)

    def mep_systems_for(self, item):
        """Return MEP systems linked to a BIM item."""

        project = self.active_project

        if project is None:
            return []

        return MEPManager(project).systems_for(item)

    def mep_networks_for(self, item):
        """Return MEP networks linked to a BIM item."""

        project = self.active_project

        if project is None:
            return []

        return MEPManager(project).networks_for(item)

    def connectors_for(self, item):
        """Return MEP connectors linked to a BIM item."""

        project = self.active_project

        if project is None:
            return []

        component_ids = {component.id for component in MEPManager(project).components_for(item)}
        connectors = ConnectorManager(project).connectors_for(item)
        mep_connectors = [
            connector for connector in project.mep_connectors
            if connector.component_id in component_ids
        ]

        if mep_connectors:
            connectors.extend(mep_connectors)
        else:
            connectors.extend(
                connector for connector in project.connectors
                if connector.source_id in component_ids or connector.target_id in component_ids
            )

        unique = []
        seen = set()
        for connector in connectors:
            if connector.id not in seen:
                unique.append(connector)
                seen.add(connector.id)

        return unique

    def mep_coordination_for(self, item):
        """Return MEP coordination placeholders linked to a BIM item."""

        project = self.active_project

        if project is None:
            return {"rules": [], "clearances": [], "service_zones": []}

        return MEPManager(project).coordination_items_for(item)

    def validation_results_for(self, item):
        """Return validation results linked to a BIM item."""

        project = self.active_project

        if project is None:
            return []

        return ValidationManager(project).results_for(item)

    def model_check_results_for(self, item):
        """Return model check results linked to a BIM item."""

        project = self.active_project

        if project is None:
            return []

        return ModelCheckManager(project).results_for(item)

    def interoperability_status_for(self, item=None):
        """Return project interoperability readiness without duplicating project data."""

        project = self.active_project

        if project is None:
            return {}

        return InteroperabilityManager(project).readiness()

    def view_for(self, view):
        """Return a BIM view by object, id or name."""

        project = self.active_project

        if project is None:
            return None

        if isinstance(view, BIMView):
            return view if view in project.views else None

        return next(
            (
                item for item in project.views
                if item.id == view or item.name == view
            ),
            None,
        )

    def element_definition_for(self, item):
        """Return the element definition assigned to a type or instance."""

        return self.element_library.get_definition(getattr(item, "element_definition_id", ""))

    def element_category_for(self, item):
        """Return the element category metadata for a type or instance."""

        project = self.active_project

        if project is None:
            return None

        definition = self.element_definition_for(item)
        category_id = getattr(definition, "category_id", "") or getattr(item, "category_id", "")

        return next(
            (
                category for category in project.element_categories
                if category.id == category_id or category.name == category_id
            ),
            None,
        )

    def related_elements(self, item):
        """Return BIM instances related to a BIM instance."""

        project = self.active_project

        if project is None:
            return []

        related_ids = set(getattr(item, "element_relationships", ElementRelationships()).related_ids())

        for relationship in project.relationships:
            if relationship.source_id == getattr(item, "id", ""):
                related_ids.add(relationship.target_id)
            if relationship.target_id == getattr(item, "id", ""):
                related_ids.add(relationship.source_id)

        for connection in project.connections:
            if connection.source_id == getattr(item, "id", ""):
                related_ids.add(connection.target_id)
            if connection.target_id == getattr(item, "id", ""):
                related_ids.add(connection.source_id)

        option_ids = {
            membership.option_id
            for membership in project.option_memberships
            if membership.element_id == getattr(item, "id", "")
        }
        for membership in project.option_memberships:
            if membership.option_id in option_ids:
                related_ids.add(membership.element_id)

        return [
            instance for instance in project.instances
            if instance.id in related_ids or instance.guid in related_ids
        ]

    def property_sets_for(self, owner):
        """Return property sets assigned to a family, type or instance."""

        project = self.active_project

        if project is None:
            return []

        owner_id = getattr(owner, "id", owner)
        property_ids = set(getattr(owner, "property_set_ids", []))

        return [
            item for item in project.property_sets
            if item.owner_id == owner_id or item.id in property_ids
        ]

    def resolved_instance_properties(self, instance):
        """Return type defaults, property sets and instance overrides for an instance."""

        resolved = {}
        project = self.active_project

        if project is None:
            return resolved

        item_type = next(
            (item for item in project.types if item.id == getattr(instance, "type_id", "")),
            None,
        )

        if item_type is not None:
            resolved.update(item_type.type_defaults.to_dict())
            definition = self.element_definition_for(item_type)
            if definition is not None:
                resolved.update(_element_parameter_values(definition.parameters))
            for property_set in self.property_sets_for(item_type):
                resolved.update(_property_set_values(property_set))

        definition = self.element_definition_for(instance)
        if definition is not None:
            resolved.update(_element_parameter_values(definition.parameters))

        resolved.update(_element_parameter_values(instance.element_parameters))
        for property_set in self.property_sets_for(instance):
            resolved.update(_property_set_values(property_set))

        resolved.update(instance.instance_parameters.to_dict())
        resolved.update(instance.instance_overrides.to_dict())

        return resolved

    def project_browser(self):
        """Return a Project Browser hierarchy without owning UI state."""

        project = self.active_project

        if project is None:
            return {"project": None, "sites": []}

        return {
            "project": project.name,
            "sites": [
                {
                    "id": site.id,
                    "name": site.name,
                    "buildings": [
                        self._building_browser(building, project)
                        for building in project.buildings
                        if building.site_id in ("", site.id)
                    ],
                }
                for site in project.sites
            ],
            "unassigned_buildings": [
                self._building_browser(building, project)
                for building in project.buildings
                if building.site_id and not any(site.id == building.site_id for site in project.sites)
            ],
        }

    def _building_browser(self, building, project):
        """Return one building hierarchy branch."""

        return {
            "id": building.id,
            "name": building.name,
            "levels": [
                {"id": level.id, "name": level.name, "elevation": level.elevation}
                for level in project.levels
                if level.building_id in ("", building.id)
            ],
            "grids": [
                {"id": grid.id, "name": grid.name}
                for grid in project.grids
                if grid.building_id in ("", building.id)
            ],
            "grid_lines": [
                {"id": line.id, "name": line.name}
                for line in project.grid_lines
            ],
            "views": [
                {"id": view.id, "name": view.name, "view_type": view.view_type}
                for view in project.views
            ],
            "sheets": [
                {"id": sheet.id, "name": sheet.name, "number": sheet.number}
                for sheet in project.sheets
            ],
            "objects": [
                {
                    "id": item.id,
                    "name": item.name,
                    "guid": item.guid,
                    "family_id": getattr(item, "family_id", ""),
                    "type_id": getattr(item, "type_id", ""),
                    "element_definition_id": getattr(item, "element_definition_id", ""),
                }
                for item in project.instances
                if item.building_id in ("", building.id)
            ],
            "families": [
                {"id": family.id, "name": family.name}
                for family in project.families
            ],
            "elements": [
                {"id": definition.id, "name": definition.name, "kind": definition.kind}
                for definition in project.element_definitions
            ],
            "assemblies": [
                {"id": assembly.id, "name": assembly.name, "members": len(assembly.members)}
                for assembly in project.assemblies
            ],
        }

    def clear(self):
        """Remove all BIM projects and browser state."""

        self.projects.clear()
        self.active_project_id = None
        self.browser_state.clear()

    def to_dict(self):
        """Return JSON-safe BIM manager data."""

        return {
            "active_project_id": self.active_project_id,
            "visible": self.visible,
            "browser_state": dict(self.browser_state),
            "projects": [project.to_dict() for project in self.projects],
        }

    def from_dict(self, data):
        """Restore BIM manager data."""

        data = data or {}
        self.projects = [BIMProject.from_dict(item) for item in data.get("projects", [])]
        self.active_project_id = data.get("active_project_id")
        self.visible = bool(data.get("visible", True))
        self.browser_state = dict(data.get("browser_state", {}))

    def relink_scene_entities(self, entities):
        """Relink BIM instances to existing 3D entities by persisted ID."""

        by_id = {}

        for entity in entities:
            entity_id = getattr(entity, "id", None)

            if entity_id:
                by_id[entity_id] = entity

            by_id[getattr(entity, "name", "")] = entity

        for instance in self.visible_instances():
            instance.entity = (
                by_id.get(instance.mesh_entity_id) or
                by_id.get(instance.mesh_entity_name)
            )


def _visible_items(project, attribute):
    if project is None:
        return []

    return [item for item in getattr(project, attribute, []) if getattr(item, "visible", True)]


def _schedule_sources(schedule, project):
    schedule_type = schedule.schedule_type.lower()

    if schedule_type == "material":
        return list(project.materials)
    if schedule_type == "quantity":
        return list(project.quantity_items)
    if schedule_type == "custom":
        return list(project.instances)

    return [
        instance for instance in project.instances
        if _element_kind(project, instance).lower() == schedule_type
    ]


def _schedule_values(item, fields, project):
    if not fields:
        fields = [ScheduleField("Name", "name"), ScheduleField("Type", "type_name")]

    return {
        field.name: _schedule_value(item, field.source, project)
        for field in fields
        if field.visible
    }


def _schedule_value(item, source, project):
    if source in ("name", "id", "type_name"):
        return getattr(item, source, "")
    if source == "category":
        return _element_kind(project, item)
    if source == "level":
        level_id = getattr(item, "level_id", "")
        level = _find_by_id(project.levels, level_id)
        return getattr(level, "name", "")
    if source == "material":
        assignment_id = getattr(item, "material_assignment_id", "")
        assignment = _find_by_id(project.material_assignments, assignment_id)
        material = _find_by_id(project.materials, getattr(assignment, "material_id", ""))
        return getattr(material, "name", "")
    if source == "quantity_type":
        return getattr(item, "quantity_type", "")
    if source == "quantity_value":
        return getattr(item, "value", "")
    if source == "unit":
        return getattr(item, "unit", "")

    return getattr(item, source, "")


def _element_kind(project, item):
    definition = _find_by_id(project.element_definitions, getattr(item, "element_definition_id", ""))

    if definition is not None:
        return getattr(definition, "kind", "")

    return getattr(item, "type_name", "")


def _inverse_relationship_name(name):
    return {
        "Parent": "Child",
        "Child": "Parent",
        "Host": "Hosted",
        "Hosted": "Host",
        "Contained": "Container",
        "Container": "Contained",
        "Adjacent": "Adjacent",
        "Connected": "Connected",
        "Dependent": "Dependency",
        "Reference": "Referenced By",
        "Aggregation": "Aggregated By",
        "Grouping": "Grouped By",
    }.get(name, "Related")


def _view_class_for(view_type):
    mapping = {
        "FloorPlan": FloorPlanView,
        "CeilingPlan": CeilingPlanView,
        "Elevation": ElevationView,
        "Section": SectionView,
        "Detail": DetailView,
        "3D View": View3D,
    }

    return mapping.get(view_type, View3D)


def _property_set_values(property_set):
    values = {}

    for definition in property_set.definitions:
        value = property_set.value_for(definition.name)

        if value is not None:
            values[definition.name] = value.value

    return values


def _element_parameter_values(parameters):
    values = {}

    for key, value in parameters.to_dict().items():
        if value in ("", None, False):
            continue

        if isinstance(value, dict) and not value:
            continue

        values[key] = value

    return values


def _bim_field_value(item, field_name):
    if not field_name:
        return None

    value = getattr(item, field_name, None)

    if value not in ("", None, False):
        return value

    for attr_name in ("instance_parameters", "instance_overrides", "element_parameters"):
        parameter_source = getattr(item, attr_name, None)

        if parameter_source is None or not hasattr(parameter_source, "to_dict"):
            continue

        data = parameter_source.to_dict()
        value = data.get(field_name)

        if value not in ("", None, False):
            return value

    property_sets = getattr(item, "property_sets", {})

    if isinstance(property_sets, dict):
        direct = property_sets.get(field_name)

        if direct not in ("", None, False):
            return direct

        for values in property_sets.values():
            if not isinstance(values, dict):
                continue

            value = values.get(field_name)

            if value not in ("", None, False):
                return value

    return None


def _instance_quantities(instance):
    box = getattr(instance, "bounding_box3d", None)
    name = getattr(instance, "name", "")
    source_id = getattr(instance, "id", "")
    items = [QuantityItem(source_id, name, "Count", 1.0, "item")]

    if box is None or not getattr(box, "valid", False):
        return items

    size = box.size
    length = max(size.x, size.y, size.z)
    area = 2.0 * (
        size.x * size.y +
        size.y * size.z +
        size.x * size.z
    )
    volume = size.x * size.y * size.z
    items.append(QuantityItem(source_id, name, "Length", length, "model_unit"))
    items.append(QuantityItem(source_id, name, "Area", area, "square_model_unit"))
    items.append(QuantityItem(source_id, name, "Volume", volume, "cubic_model_unit"))
    items.append(QuantityItem(source_id, name, "Weight", 0.0, "placeholder"))
    items.append(QuantityItem(source_id, name, "Cost", 0.0, "placeholder"))

    return items


def _find_by_id(items, identifier):
    for item in items:
        if getattr(item, "id", None) == identifier:
            return item

    return None


def _marker_data(marker, extra):
    data = {
        "id": marker.id,
        "name": marker.name,
        "visible": marker.visible,
        "locked": marker.locked,
        "selected": marker.selected,
        "layer_name": marker.layer_name,
    }
    data.update(extra)

    return data


def _restore_marker(marker, data):
    marker.id = data.get("id", marker.id)
    marker.visible = bool(data.get("visible", True))
    marker.locked = bool(data.get("locked", False))
    marker.selected = bool(data.get("selected", False))
    marker.layer_name = data.get("layer_name")


def _vector_to_data(point):
    return {"x": point.x, "y": point.y, "z": point.z}


def _vector_from_data(data):
    data = data or {}

    return Vector3(
        float(data.get("x", 0.0)),
        float(data.get("y", 0.0)),
        float(data.get("z", 0.0)),
    )

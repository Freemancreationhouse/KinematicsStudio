"""Machine Workspace manufacturing configuration foundation.

The Machine Workspace is a Workspace-owned manufacturing metadata facade.
It reuses ProductManager storage for machine, tool and material records and
does not perform slicing, toolpath generation, G-code generation, simulation or
machine communication.
"""

from dataclasses import dataclass, field
from uuid import uuid4

from engine.product import (
    EngineeringMaterial,
    MachineCapabilities,
    MachineMetadata,
    MaterialMetadata,
    ToolMetadata,
)


MACHINE_WORKSPACE_SETTINGS_KEY = "machine_workspace"


@dataclass
class MachineWorkspaceState:
    """Serializable activation state for the Workspace-owned machine area."""

    active: bool = False
    workspace_name: str = "Machine Workspace"
    active_machine_id: str = ""
    active_profile_id: str = ""
    active_tool_library_id: str = ""
    active_material_id: str = ""
    version: str = "1.7"
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe state data."""

        return {
            "active": self.active,
            "workspace_name": self.workspace_name,
            "active_machine_id": self.active_machine_id,
            "active_profile_id": self.active_profile_id,
            "active_tool_library_id": self.active_tool_library_id,
            "active_material_id": self.active_material_id,
            "version": self.version,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create state from persisted project data."""

        data = data or {}
        return MachineWorkspaceState(
            bool(data.get("active", False)),
            data.get("workspace_name", "Machine Workspace"),
            data.get("active_machine_id", ""),
            data.get("active_profile_id", ""),
            data.get("active_tool_library_id", ""),
            data.get("active_material_id", ""),
            data.get("version", "1.7"),
            dict(data.get("metadata", {})),
        )


@dataclass
class ManufacturingPreferences:
    """Persistent user/workspace manufacturing preferences."""

    preferred_machine_id: str = ""
    preferred_units: str = "mm"
    preferred_tool_library_id: str = ""
    preferred_material_id: str = ""
    preferred_firmware: str = ""
    preferred_workflow: str = ""
    preferred_safety_profile: str = ""
    properties: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe preference data."""

        return {
            "preferred_machine_id": self.preferred_machine_id,
            "preferred_units": self.preferred_units,
            "preferred_tool_library_id": self.preferred_tool_library_id,
            "preferred_material_id": self.preferred_material_id,
            "preferred_firmware": self.preferred_firmware,
            "preferred_workflow": self.preferred_workflow,
            "preferred_safety_profile": self.preferred_safety_profile,
            "properties": dict(self.properties),
        }

    @staticmethod
    def from_dict(data):
        """Create preferences from persisted project data."""

        data = data or {}
        return ManufacturingPreferences(
            data.get("preferred_machine_id", ""),
            data.get("preferred_units", "mm"),
            data.get("preferred_tool_library_id", ""),
            data.get("preferred_material_id", ""),
            data.get("preferred_firmware", ""),
            data.get("preferred_workflow", ""),
            data.get("preferred_safety_profile", ""),
            dict(data.get("properties", {})),
        )


@dataclass
class MachineWorkspaceValidation:
    """Validation report for manufacturing configuration metadata."""

    valid: bool = True
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def add_error(self, message):
        """Record a validation error."""

        self.valid = False
        self.errors.append(str(message))

    def add_warning(self, message):
        """Record a validation warning."""

        self.warnings.append(str(message))

    def to_dict(self):
        """Return JSON-safe validation data."""

        return {
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


@dataclass
class MachineWorkspaceDiagnostics:
    """Diagnostics summary for Machine Workspace configuration metadata."""

    registered_machines: int = 0
    profiles: int = 0
    tools: int = 0
    materials: int = 0
    workspace_statistics: dict = field(default_factory=dict)
    activation_statistics: dict = field(default_factory=dict)
    validation_statistics: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe diagnostics data."""

        return {
            "registered_machines": self.registered_machines,
            "profiles": self.profiles,
            "tools": self.tools,
            "materials": self.materials,
            "workspace_statistics": dict(self.workspace_statistics),
            "activation_statistics": dict(self.activation_statistics),
            "validation_statistics": dict(self.validation_statistics),
        }


class MachineWorkspace:
    """Workspace-owned manufacturing configuration facade.

    This object is not a manager and not a second workspace. It coordinates
    machine workspace state while reusing ProductManager collections for
    machines, profiles, tools and materials.
    """

    MACHINE_CATEGORIES = {
        "FDM Printer": "FDM",
        "SLA Printer": "SLA",
        "CNC Mill": "CNC",
        "CNC Router": "Router",
        "Laser Cutter": "Laser",
        "Plasma Cutter": "Plasma",
        "Waterjet": "Generic",
        "Robot": "Generic",
        "Custom Machine": "Generic",
    }

    def __init__(self, workspace):

        self.workspace = workspace
        self.state = MachineWorkspaceState()
        self.preferences = ManufacturingPreferences()
        self.last_validation = MachineWorkspaceValidation()
        self.last_diagnostics = MachineWorkspaceDiagnostics()
        self.activation_count = 0
        self.validation_count = 0
        self.load_from_settings()

    @property
    def product_manager(self):
        """Return the existing ProductManager owned by Workspace."""

        return self.workspace.product_manager

    def initialize(self):
        """Initialize the machine workspace state without creating runtime systems."""

        self._save()
        return self

    def activate(self, workspace_name=None):
        """Activate the machine workspace metadata area."""

        self.state.active = True
        if workspace_name:
            self.state.workspace_name = str(workspace_name)
        self.activation_count += 1
        self._save()
        return self.state

    def deactivate(self):
        """Deactivate the machine workspace metadata area."""

        self.state.active = False
        self._save()
        return self.state

    def switch_to(self, workspace_name="Machine Workspace"):
        """Switch Workspace UI state to the machine workspace metadata area."""

        return self.activate(workspace_name)

    def clear(self):
        """Clear machine workspace activation state and preferences only."""

        self.state = MachineWorkspaceState()
        self.preferences = ManufacturingPreferences()
        self.last_validation = MachineWorkspaceValidation()
        self.last_diagnostics = MachineWorkspaceDiagnostics()
        self.activation_count = 0
        self.validation_count = 0
        self.workspace.project_settings.pop(MACHINE_WORKSPACE_SETTINGS_KEY, None)

    def register_machine(
        self,
        name,
        category,
        manufacturer="",
        model="",
        firmware="",
        capabilities=None,
        work_envelope=None,
        supported_materials=None,
        supported_tool_systems=None,
        supported_file_formats=None,
        machine_id=None,
    ):
        """Register a manufacturing machine definition in ProductManager."""

        if not name:
            raise ValueError("Machine name is required.")
        if category not in self.MACHINE_CATEGORIES:
            raise ValueError(f"Unsupported machine category: {category}")
        if machine_id and self._id_exists(self.product_manager.machine_definitions, machine_id):
            raise ValueError(f"Duplicate machine ID: {machine_id}")
        if self._name_exists(self.product_manager.machine_definitions, name):
            raise ValueError(f"Duplicate machine name: {name}")

        library = self._default_machine_library()
        properties = {
            "machine_workspace": True,
            "supported_materials": list(supported_materials or []),
            "supported_tool_systems": list(supported_tool_systems or []),
            "supported_file_formats": list(supported_file_formats or []),
        }
        if work_envelope:
            properties["work_envelope"] = dict(work_envelope)

        metadata = MachineMetadata(
            manufacturer=manufacturer,
            model=model,
            firmware=firmware,
            machine_category=category,
            properties=properties,
        )
        machine = self.product_manager.machine_library_manager.create_machine(
            self.MACHINE_CATEGORIES[category],
            library=library,
            name=name,
            category=category,
            metadata=metadata,
            capabilities=capabilities or MachineCapabilities(),
        )
        if machine_id:
            machine.id = machine_id
        self._save()
        return machine

    def create_profile(self, machine, name, tool_library=None, version="1.0", metadata=None):
        """Create an editable machine profile linked to an existing machine."""

        target = self.product_manager.machine_library_manager.machine_for(machine)
        if target is None:
            raise ValueError("Machine profile requires a registered machine.")
        if self._name_exists(self.product_manager.machine_profiles, name):
            raise ValueError(f"Duplicate machine profile name: {name}")

        profile_metadata = metadata or MachineMetadata(
            machine_category="Machine Profile",
            properties={
                "machine_workspace": True,
                "version": version,
            },
        )
        profile = self.product_manager.machine_library_manager.create_profile(
            target,
            tool_library=tool_library,
            name=name,
            metadata=profile_metadata,
        )
        self._save()
        return profile

    def edit_profile(self, profile, **changes):
        """Edit profile metadata without changing geometry or execution state."""

        target = self.product_manager.machine_library_manager.profile_for(profile)
        if target is None:
            raise ValueError("Machine profile was not found.")

        if "name" in changes:
            new_name = changes["name"]
            if new_name != target.name and self._name_exists(self.product_manager.machine_profiles, new_name):
                raise ValueError(f"Duplicate machine profile name: {new_name}")
            target.name = new_name
        if "enabled" in changes:
            target.enabled = bool(changes["enabled"])
        if "tool_library" in changes:
            target.tool_library_id = getattr(changes["tool_library"], "id", changes["tool_library"]) or ""
        if "version" in changes:
            self._metadata_properties(target)["version"] = changes["version"]
        for key, value in changes.get("metadata", {}).items():
            self._metadata_properties(target)[key] = value
        self._save()
        return target

    def clone_profile(self, profile, name):
        """Clone a machine profile as an editable independent profile."""

        source = self.product_manager.machine_library_manager.profile_for(profile)
        if source is None:
            raise ValueError("Machine profile was not found.")
        if self._name_exists(self.product_manager.machine_profiles, name):
            raise ValueError(f"Duplicate machine profile name: {name}")

        clone = self.product_manager.machine_library_manager.create_profile(
            source.machine_id,
            tool_library=source.tool_library_id,
            name=name,
            enabled=source.enabled,
            metadata=getattr(source, "metadata", None),
        )
        self._save()
        return clone

    def activate_profile(self, profile):
        """Activate an existing machine profile for the workspace."""

        target = self.product_manager.machine_library_manager.profile_for(profile)
        if target is None:
            raise ValueError("Machine profile was not found.")
        self.state.active_profile_id = target.id
        self.state.active_machine_id = target.machine_id
        self.state.active_tool_library_id = target.tool_library_id
        self.preferences.preferred_machine_id = target.machine_id
        self.preferences.preferred_tool_library_id = target.tool_library_id
        self._save()
        return target

    def create_tool_library(self, name="Tool Library"):
        """Create a ProductManager-backed tool library."""

        if self._name_exists(self.product_manager.tool_libraries, name):
            raise ValueError(f"Duplicate tool library name: {name}")
        library = self.product_manager.tool_library_manager.create_library(name)
        self._save()
        return library

    def register_tool(
        self,
        library,
        name,
        category,
        diameter=0.0,
        length=0.0,
        material="",
        operating_limits=None,
        manufacturer="",
        status="Available",
        tool_id=None,
    ):
        """Register a tool definition in the existing ToolLibrary."""

        target_library = self.product_manager.tool_library_manager.library_for(library)
        if target_library is None:
            raise ValueError("Tool library was not found.")
        if tool_id and self._id_exists(self.product_manager.tool_definitions, tool_id):
            raise ValueError(f"Duplicate tool ID: {tool_id}")
        if any(tool.name == name and tool.library_id == target_library.id for tool in self.product_manager.tool_definitions):
            raise ValueError(f"Duplicate tool name in library: {name}")

        target_category = next(
            (
                item for item in self.product_manager.tool_categories
                if item.library_id == target_library.id and item.name == category
            ),
            None,
        )
        if target_category is None:
            target_category = self.product_manager.tool_library_manager.create_category(target_library, category)

        metadata = ToolMetadata(
            manufacturer=manufacturer,
            material=material,
            properties={
                "machine_workspace": True,
                "operating_limits": dict(operating_limits or {}),
                "status": status,
            },
        )
        tool = self.product_manager.tool_library_manager.create_tool(
            "ToolDefinition",
            library=target_library,
            category=target_category,
            name=name,
            tool_type=category,
            diameter=diameter,
            overall_length=length,
            metadata=metadata,
        )
        if tool_id:
            tool.id = tool_id
        self._save()
        return tool

    def register_material(
        self,
        name,
        category,
        density=0.0,
        color="#b0bec5",
        manufacturing_notes="",
        compatible_machines=None,
        default_process_metadata=None,
        material_id=None,
    ):
        """Register an engineering material with manufacturing metadata."""

        if material_id and self._id_exists(self.product_manager.engineering_materials, material_id):
            raise ValueError(f"Duplicate material ID: {material_id}")
        if self._name_exists(self.product_manager.engineering_materials, name):
            raise ValueError(f"Duplicate material name: {name}")

        self.product_manager.engineering_material_manager.ensure_default_categories()
        material_category = next(
            (item for item in self.product_manager.material_categories if item.name == category),
            None,
        )
        if material_category is None:
            from engine.product import MaterialCategory

            material_category = self.product_manager.engineering_material_manager.add_item(MaterialCategory(category, color))

        metadata = MaterialMetadata(
            description=manufacturing_notes,
            source="Machine Workspace",
            properties={
                "machine_workspace": True,
                "compatible_machines": [
                    getattr(machine, "id", machine) for machine in compatible_machines or []
                ],
                "default_process_metadata": dict(default_process_metadata or {}),
            },
        )
        material = EngineeringMaterial(
            name=name,
            category_id=material_category.id,
            density=density,
            metadata=metadata,
            color=color,
            id=material_id or str(uuid4()),
        )
        self.product_manager.engineering_material_manager.add_item(material)
        self._save()
        return material

    def set_preferences(self, **preferences):
        """Update persistent machine workspace preferences."""

        for key, value in preferences.items():
            if hasattr(self.preferences, key):
                setattr(self.preferences, key, getattr(value, "id", value) or "")
            else:
                self.preferences.properties[key] = value
        self._save()
        return self.preferences

    def validate(self):
        """Validate machine workspace metadata without executing manufacturing."""

        report = MachineWorkspaceValidation()
        self._validate_unique_ids(report, "machine", self.product_manager.machine_definitions)
        self._validate_unique_ids(report, "machine profile", self.product_manager.machine_profiles)
        self._validate_unique_ids(report, "tool", self.product_manager.tool_definitions)
        self._validate_unique_ids(report, "material", self.product_manager.engineering_materials)
        self._validate_unique_names(report, "machine", self.product_manager.machine_definitions)
        self._validate_unique_names(report, "machine profile", self.product_manager.machine_profiles)

        machine_ids = {machine.id for machine in self.product_manager.machine_definitions}
        tool_library_ids = {library.id for library in self.product_manager.tool_libraries}
        for profile in self.product_manager.machine_profiles:
            if profile.machine_id and profile.machine_id not in machine_ids:
                report.add_error(f"Machine profile '{profile.name}' references a missing machine.")
            if profile.tool_library_id and profile.tool_library_id not in tool_library_ids:
                report.add_error(f"Machine profile '{profile.name}' references a missing tool library.")

        for machine in self.product_manager.machine_definitions:
            metadata = getattr(machine, "metadata", None)
            if not getattr(machine, "category", ""):
                report.add_error(f"Machine '{machine.name}' is missing category metadata.")
            properties = getattr(metadata, "properties", {}) if metadata else {}
            if not properties.get("supported_file_formats"):
                report.add_warning(f"Machine '{machine.name}' has no supported file format metadata.")

        for material in self.product_manager.engineering_materials:
            machine_refs = material.metadata.properties.get("compatible_machines", [])
            for machine_id in machine_refs:
                if machine_id not in machine_ids:
                    report.add_error(f"Material '{material.name}' references a missing compatible machine.")

        self.validation_count += 1
        self.last_validation = report
        self._save()
        return report

    def diagnostics(self):
        """Return current Machine Workspace diagnostics."""

        diagnostics = MachineWorkspaceDiagnostics(
            registered_machines=len(self.product_manager.machine_definitions),
            profiles=len(self.product_manager.machine_profiles),
            tools=len(self.product_manager.tool_definitions),
            materials=len(self.product_manager.engineering_materials),
            workspace_statistics={
                "active": self.state.active,
                "workspace_name": self.state.workspace_name,
            },
            activation_statistics={
                "activation_count": self.activation_count,
                "active_profile_id": self.state.active_profile_id,
            },
            validation_statistics={
                "validation_count": self.validation_count,
                "last_valid": self.last_validation.valid,
                "errors": len(self.last_validation.errors),
                "warnings": len(self.last_validation.warnings),
            },
        )
        self.last_diagnostics = diagnostics
        self._save()
        return diagnostics

    def to_dict(self):
        """Return JSON-safe machine workspace data for project settings."""

        return {
            "state": self.state.to_dict(),
            "preferences": self.preferences.to_dict(),
            "last_validation": self.last_validation.to_dict(),
            "last_diagnostics": self.last_diagnostics.to_dict(),
            "activation_count": self.activation_count,
            "validation_count": self.validation_count,
        }

    def load_from_settings(self):
        """Restore machine workspace state from Workspace project settings."""

        data = self.workspace.project_settings.get(MACHINE_WORKSPACE_SETTINGS_KEY, {})
        self.state = MachineWorkspaceState.from_dict(data.get("state", {}))
        self.preferences = ManufacturingPreferences.from_dict(data.get("preferences", {}))
        validation_data = data.get("last_validation", {})
        self.last_validation = MachineWorkspaceValidation(
            bool(validation_data.get("valid", True)),
            list(validation_data.get("errors", [])),
            list(validation_data.get("warnings", [])),
        )
        diagnostics_data = data.get("last_diagnostics", {})
        self.last_diagnostics = MachineWorkspaceDiagnostics(
            int(diagnostics_data.get("registered_machines", 0)),
            int(diagnostics_data.get("profiles", 0)),
            int(diagnostics_data.get("tools", 0)),
            int(diagnostics_data.get("materials", 0)),
            dict(diagnostics_data.get("workspace_statistics", {})),
            dict(diagnostics_data.get("activation_statistics", {})),
            dict(diagnostics_data.get("validation_statistics", {})),
        )
        self.activation_count = int(data.get("activation_count", 0))
        self.validation_count = int(data.get("validation_count", 0))
        return self

    def _save(self):
        self.workspace.project_settings[MACHINE_WORKSPACE_SETTINGS_KEY] = self.to_dict()

    def _default_machine_library(self):
        library = self.product_manager.machine_library_manager.library_for("Machine Workspace Library")
        if library is None:
            library = self.product_manager.machine_library_manager.create_library("Machine Workspace Library")
        return library

    @staticmethod
    def _metadata_properties(item):
        metadata = getattr(item, "metadata", None)
        if isinstance(metadata, dict):
            return metadata
        if metadata is None:
            item.metadata = {}
            return item.metadata
        properties = getattr(metadata, "properties", None)
        if properties is None:
            metadata.properties = {}
            return metadata.properties
        return properties

    @staticmethod
    def _id_exists(collection, identifier):
        return any(getattr(item, "id", None) == identifier for item in collection)

    @staticmethod
    def _name_exists(collection, name):
        return any(getattr(item, "name", None) == name for item in collection)

    @staticmethod
    def _validate_unique_ids(report, label, collection):
        seen = set()
        for item in collection:
            identifier = getattr(item, "id", "")
            if not identifier:
                report.add_error(f"{label.title()} '{getattr(item, 'name', '')}' is missing an ID.")
            elif identifier in seen:
                report.add_error(f"Duplicate {label} ID: {identifier}")
            seen.add(identifier)

    @staticmethod
    def _validate_unique_names(report, label, collection):
        seen = set()
        for item in collection:
            name = getattr(item, "name", "")
            if name in seen:
                report.add_error(f"Duplicate {label} name: {name}")
            seen.add(name)

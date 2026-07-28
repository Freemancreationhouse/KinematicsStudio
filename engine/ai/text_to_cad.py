import re
import time
from dataclasses import dataclass, field
from uuid import uuid4

from engine.commands.ai_cad_command import AIParametricCADCommand
from engine.commands.product_command import (
    AddProductFeatureCommand,
    AddProductObjectCommand,
    ExecuteFeatureGeometryCommand,
)
from engine.geometry import Vector3
from engine.product import (
    Constraint,
    FeatureOptions,
    ProductMetadata,
    ProductPart,
    Sketch,
    SketchCircle,
    SketchDimension,
    SketchLoop,
    SketchProfile,
    SketchRectangle,
)


class TextToCADValidationError(ValueError):
    """Raised when a natural-language CAD request cannot be executed safely."""


@dataclass
class CADIntent:
    """Engineering intent inferred from the request."""

    domain: str = "general"
    manufacturing: str = ""
    environment: str = ""
    structural: str = ""
    properties: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe intent metadata."""

        return {
            "domain": self.domain,
            "manufacturing": self.manufacturing,
            "environment": self.environment,
            "structural": self.structural,
            "properties": dict(self.properties),
        }


@dataclass
class CADPlanStep:
    """One planned editable parametric CAD operation."""

    action: str
    target: str
    parameters: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe plan step metadata."""

        return {
            "action": self.action,
            "target": self.target,
            "parameters": dict(self.parameters),
        }


@dataclass
class TextToCADPlan:
    """Executable text-to-parametric CAD plan."""

    prompt: str
    object_type: str
    dimensions: dict
    unit: str
    intent: CADIntent
    steps: list
    warnings: list = field(default_factory=list)
    resolved_entities: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe plan metadata."""

        return {
            "id": self.id,
            "prompt": self.prompt,
            "object_type": self.object_type,
            "dimensions": dict(self.dimensions),
            "unit": self.unit,
            "intent": self.intent.to_dict(),
            "steps": [step.to_dict() for step in self.steps],
            "warnings": list(self.warnings),
            "resolved_entities": dict(self.resolved_entities),
        }


@dataclass
class TextToCADResult:
    """Result of a completed text-to-parametric CAD request."""

    plan: TextToCADPlan
    command: AIParametricCADCommand
    explanation: dict
    diagnostics: dict

    def to_dict(self):
        """Return JSON-safe execution result metadata."""

        return {
            "plan": self.plan.to_dict(),
            "command": self.command.name,
            "explanation": dict(self.explanation),
            "diagnostics": dict(self.diagnostics),
        }


class TextToParametricCADEngine:
    """Converts engineering language into executable parametric CAD commands."""

    OBJECT_ALIASES = {
        "box": "box",
        "cube": "box",
        "block": "box",
        "enclosure": "enclosure",
        "case": "enclosure",
        "housing": "enclosure",
        "bookshelf": "bookshelf",
        "shelf": "bookshelf",
        "desk lamp": "desk_lamp",
        "lamp": "desk_lamp",
        "flange": "flange",
        "shaft": "shaft",
        "pipe": "pipe",
        "tube": "pipe",
        "wall": "wall",
        "staircase": "staircase",
        "stairs": "staircase",
        "table": "table",
    }
    DEFAULTS = {
        "box": {"length": 100.0, "width": 60.0, "height": 40.0},
        "enclosure": {"length": 120.0, "width": 80.0, "height": 40.0, "wall_thickness": 2.5},
        "bookshelf": {"length": 800.0, "width": 260.0, "height": 1200.0, "shelves": 4},
        "desk_lamp": {"diameter": 120.0, "height": 420.0, "arm_length": 260.0},
        "flange": {"diameter": 120.0, "height": 12.0, "hole_diameter": 40.0},
        "shaft": {"diameter": 25.0, "length": 120.0},
        "pipe": {"diameter": 50.0, "length": 200.0, "wall_thickness": 3.0},
        "wall": {"length": 3000.0, "width": 150.0, "height": 2400.0},
        "staircase": {"length": 3000.0, "width": 900.0, "height": 2700.0, "steps": 12},
        "table": {"length": 1200.0, "width": 700.0, "height": 750.0},
    }
    UNIT_SCALE = {
        "mm": 1.0,
        "millimeter": 1.0,
        "millimeters": 1.0,
        "cm": 10.0,
        "centimeter": 10.0,
        "centimeters": 10.0,
        "m": 1000.0,
        "meter": 1000.0,
        "meters": 1000.0,
        "in": 25.4,
        "inch": 25.4,
        "inches": 25.4,
        "ft": 304.8,
        "foot": 304.8,
        "feet": 304.8,
    }
    INTENT_KEYWORDS = {
        "load bearing": ("structural", "load_bearing"),
        "lightweight": ("structural", "lightweight"),
        "waterproof": ("environment", "waterproof"),
        "outdoor": ("environment", "outdoor"),
        "injection molded": ("manufacturing", "injection_molded"),
        "3d printable": ("manufacturing", "3d_printable"),
        "3d printed": ("manufacturing", "3d_printable"),
        "laser cut": ("manufacturing", "laser_cut"),
        "cnc machined": ("manufacturing", "cnc_machined"),
        "architectural": ("domain", "architectural"),
        "furniture": ("domain", "furniture"),
        "mechanical": ("domain", "mechanical"),
        "consumer product": ("domain", "consumer_product"),
    }

    def __init__(self):

        self.statistics = {
            "requests": 0,
            "successful": 0,
            "failed": 0,
            "planning_time_ms": 0.0,
            "execution_time_ms": 0.0,
            "validation_failures": 0,
            "conversation_resolutions": 0,
            "commands_generated": 0,
        }
        self.last_plan = None

    def plan(self, prompt, workspace=None, session=None):
        """Create an executable command plan without mutating the workspace."""

        started = time.perf_counter()
        text = self._normalize_prompt(prompt)
        object_type = self._object_type(text, session)
        dimensions, unit, warnings = self._dimensions(text, object_type)
        intent = self._intent(text, object_type)
        resolved = self._resolve_entities(text, workspace, session)
        steps = self._steps_for(object_type, dimensions, unit, intent)
        plan = TextToCADPlan(prompt, object_type, dimensions, unit, intent, steps, warnings, resolved)
        self._validate_plan(plan, workspace)
        self.last_plan = plan
        self.statistics["planning_time_ms"] += (time.perf_counter() - started) * 1000.0
        return plan

    def execute(self, prompt, workspace, session=None):
        """Plan and execute a text-to-parametric CAD command sequence."""

        self.statistics["requests"] += 1
        try:
            plan = self.plan(prompt, workspace, session)
            commands = self.commands_for_plan(plan, workspace)
            command = AIParametricCADCommand(workspace, plan, commands)
            started = time.perf_counter()
            workspace.command_manager.execute(command)
            self.statistics["execution_time_ms"] += (time.perf_counter() - started) * 1000.0
            self.statistics["successful"] += 1
            self.statistics["commands_generated"] += len(commands)
            explanation = self.explain(plan, commands)
            self._remember_session(session, prompt, explanation)
            return TextToCADResult(plan, command, explanation, self.diagnostics())
        except Exception:
            self.statistics["failed"] += 1
            raise

    def commands_for_plan(self, plan, workspace):
        """Generate production commands from a validated plan."""

        part, sketch, geometry, profile, feature = self._objects_for_plan(plan)
        commands = [
            AddProductObjectCommand(workspace, part),
            AddProductObjectCommand(workspace, sketch),
        ]
        for item in geometry:
            commands.append(AddProductObjectCommand(workspace, item))
        commands.append(AddProductObjectCommand(workspace, profile))
        commands.append(AddProductFeatureCommand(workspace, feature))
        commands.append(ExecuteFeatureGeometryCommand(workspace, feature))
        return commands

    def explain(self, plan, commands):
        """Explain the intent, entity resolution, plan and generated commands."""

        return {
            "intent": plan.intent.to_dict(),
            "resolved_entities": dict(plan.resolved_entities),
            "feature_plan": [step.to_dict() for step in plan.steps],
            "commands_generated": [command.__class__.__name__ for command in commands],
            "features_modified": [step.target for step in plan.steps if "feature" in step.action.lower()],
            "parameters_updated": dict(plan.dimensions),
            "warnings": list(plan.warnings),
            "regeneration_result": "Executed through Command System -> FeatureManager -> GeometryKernel -> BodyManager.",
        }

    def diagnostics(self):
        """Return text-to-CAD diagnostics."""

        data = dict(self.statistics)
        data["last_plan_id"] = getattr(self.last_plan, "id", "")
        data["last_object_type"] = getattr(self.last_plan, "object_type", "")
        return data

    def _objects_for_plan(self, plan):
        dimensions = plan.dimensions
        title = plan.object_type.replace("_", " ").title()
        metadata = ProductMetadata(
            description=f"AI planned editable parametric {title}",
            properties={
                "ai_text_to_cad_plan_id": plan.id,
                "intent": plan.intent.to_dict(),
                "source_prompt": plan.prompt,
                "unit": plan.unit,
            },
        )
        part = ProductPart(title, metadata=metadata)
        sketch = Sketch(f"{title} Base Sketch", part.id)
        geometry, profile = self._profile_geometry(plan, sketch)
        options = FeatureOptions(
            operation="New Body",
            direction="Positive",
            distance=float(dimensions.get("height", dimensions.get("length", 10.0))),
            merge_result=False,
        )
        feature = self._feature_for(plan, part, profile, options)
        return part, sketch, geometry, profile, feature

    def _profile_geometry(self, plan, sketch):
        dimensions = plan.dimensions
        object_type = plan.object_type
        if object_type in ("flange", "shaft", "pipe", "desk_lamp"):
            radius = float(dimensions.get("diameter", dimensions.get("width", 50.0))) / 2.0
            circle = SketchCircle(f"{plan.object_type} diameter", sketch.id, Vector3(), radius)
            dimension = SketchDimension("Diameter", radius * 2.0, plan.unit, sketch.id, [circle.id], "Driven Diameter")
            loop = SketchLoop("Circular Profile Loop", sketch.id, [circle.id], True)
            profile = SketchProfile("Circular Profile", sketch.id, [loop.id], [])
            return [circle, dimension, loop], profile
        length = float(dimensions.get("length", 100.0))
        width = float(dimensions.get("width", dimensions.get("depth", 60.0)))
        rectangle = SketchRectangle(
            f"{plan.object_type} footprint",
            sketch.id,
            Vector3(-length / 2.0, -width / 2.0, 0.0),
            Vector3(length / 2.0, width / 2.0, 0.0),
        )
        horizontal = Constraint("Horizontal", sketch.id, [rectangle.id], "Horizontal Footprint")
        vertical = Constraint("Vertical", sketch.id, [rectangle.id], "Vertical Footprint")
        length_dimension = SketchDimension("Length", length, plan.unit, sketch.id, [rectangle.id], "Driving Length")
        width_dimension = SketchDimension("Width", width, plan.unit, sketch.id, [rectangle.id], "Driving Width")
        loop = SketchLoop("Rectangular Profile Loop", sketch.id, [rectangle.id], True)
        profile = SketchProfile("Rectangular Profile", sketch.id, [loop.id], [])
        return [rectangle, horizontal, vertical, length_dimension, width_dimension, loop], profile

    def _feature_for(self, plan, part, profile, options):
        from engine.product import ExtrudeFeature, FeatureDefinition, FeatureMetadata, FeatureResult, RevolveFeature

        definition = FeatureDefinition(profile.sketch_id, profile.id, "", [], options, {
            "dimensions": dict(plan.dimensions),
            "intent": plan.intent.to_dict(),
            "ai_text_to_cad_plan_id": plan.id,
        })
        metadata = FeatureMetadata(
            "AI planned editable feature",
            "Ready",
            "AI Text-to-CAD",
            {
                "object_type": plan.object_type,
                "intent": plan.intent.to_dict(),
                "ai_text_to_cad_plan_id": plan.id,
            },
        )
        feature_class = RevolveFeature if plan.object_type in ("shaft", "pipe") else ExtrudeFeature
        feature_name = f"{plan.object_type.replace('_', ' ').title()} {'Revolve' if feature_class is RevolveFeature else 'Extrude'}"
        return feature_class(feature_name, part.id, definition, metadata, FeatureResult())

    def _steps_for(self, object_type, dimensions, unit, intent):
        steps = [
            CADPlanStep("Resolve Context", "Workspace", {"unit": unit}),
            CADPlanStep("Create Product Part", object_type, {"intent": intent.to_dict()}),
            CADPlanStep("Create Sketch", "Base Profile", {"constraint_driven": True}),
            CADPlanStep("Add Dimensions", "Base Profile", dict(dimensions)),
            CADPlanStep("Create Feature", "Primary Solid", {"feature": "Revolve" if object_type in ("shaft", "pipe") else "Extrude"}),
            CADPlanStep("Regenerate", "Body", {"path": "FeatureManager -> GeometryKernel -> BodyManager"}),
        ]
        if object_type in ("enclosure", "pipe"):
            steps.append(CADPlanStep("Capture Future Feature", "Shell/Wall Thickness", {"wall_thickness": dimensions.get("wall_thickness")}))
        if object_type in ("flange",):
            steps.append(CADPlanStep("Capture Future Feature", "Hole", {"diameter": dimensions.get("hole_diameter")}))
        return steps

    def _validate_plan(self, plan, workspace):
        if workspace is None:
            self.statistics["validation_failures"] += 1
            raise TextToCADValidationError("Workspace is required for text-to-parametric CAD execution.")
        if not hasattr(workspace, "command_manager") or not hasattr(workspace, "product_manager"):
            self.statistics["validation_failures"] += 1
            raise TextToCADValidationError("Workspace lacks the required Command System or ProductManager.")
        if plan.object_type not in self.DEFAULTS:
            self.statistics["validation_failures"] += 1
            raise TextToCADValidationError(f"Unsupported CAD object type: {plan.object_type}")
        for name, value in plan.dimensions.items():
            if isinstance(value, (int, float)) and value <= 0:
                self.statistics["validation_failures"] += 1
                raise TextToCADValidationError(f"Dimension '{name}' must be positive.")

    def _normalize_prompt(self, prompt):
        text = " ".join(str(prompt or "").strip().lower().split())
        if not text:
            self.statistics["validation_failures"] += 1
            raise TextToCADValidationError("A text-to-CAD prompt is required.")
        return text

    def _object_type(self, text, session):
        for phrase in sorted(self.OBJECT_ALIASES, key=len, reverse=True):
            if phrase in text:
                return self.OBJECT_ALIASES[phrase]
        if re.search(r"\b(it|that|the last|the selected)\b", text):
            resolved = self._conversation_object_type(session)
            if resolved:
                self.statistics["conversation_resolutions"] += 1
                return resolved
        self.statistics["validation_failures"] += 1
        raise TextToCADValidationError("The CAD object type is ambiguous or unsupported.")

    def _conversation_object_type(self, session):
        for message in reversed(getattr(session, "messages", []) or []):
            content = str(getattr(message, "content", ""))
            match = re.search(r"object_type=([a-z_]+)", content)
            if match and match.group(1) in self.DEFAULTS:
                return match.group(1)
        if self.last_plan is not None:
            return self.last_plan.object_type
        return ""

    def _dimensions(self, text, object_type):
        dimensions = dict(self.DEFAULTS[object_type])
        warnings = []
        global_unit = self._unit_from_text(text)
        triplet = re.search(
            r"(\d+(?:\.\d+)?)\s*(?:x|by)\s*(\d+(?:\.\d+)?)\s*(?:x|by)\s*(\d+(?:\.\d+)?)\s*([a-z\"']+)?",
            text,
        )
        if triplet:
            scale = self._scale(triplet.group(4) or global_unit)
            dimensions["length"] = float(triplet.group(1)) * scale
            dimensions["width"] = float(triplet.group(2)) * scale
            dimensions["height"] = float(triplet.group(3)) * scale
        for key, aliases in {
            "length": ("length", "long", "wide span"),
            "width": ("width", "wide", "depth", "deep"),
            "height": ("height", "tall", "high"),
            "diameter": ("diameter", "dia"),
            "hole_diameter": ("hole diameter", "bore"),
            "wall_thickness": ("wall thickness", "thickness"),
            "arm_length": ("arm length",),
        }.items():
            for alias in aliases:
                match = re.search(rf"{re.escape(alias)}\s*(?:of|=|:)?\s*(\d+(?:\.\d+)?)\s*([a-z\"']+)?", text)
                if match:
                    dimensions[key] = float(match.group(1)) * self._scale(match.group(2) or global_unit)
                    break
        for key, aliases in {"shelves": ("shelves", "shelf count"), "steps": ("steps", "treads")}.items():
            for alias in aliases:
                match = re.search(rf"(\d+)\s*{re.escape(alias)}", text) or re.search(rf"{re.escape(alias)}\s*(\d+)", text)
                if match:
                    dimensions[key] = int(match.group(1))
                    break
        if not re.search(r"\d", text):
            warnings.append("No dimensions supplied; engineering defaults were used.")
        return dimensions, "mm", warnings

    def _unit_from_text(self, text):
        match = re.search(r"\b(mm|millimeters?|cm|centimeters?|m|meters?|in|inch|inches|ft|foot|feet)\b", text)
        if match:
            return match.group(1)
        if '"' in text:
            return "in"
        if "'" in text:
            return "ft"
        return "mm"

    def _scale(self, unit):
        cleaned = (unit or "mm").replace('"', "in").replace("'", "ft").strip().lower()
        return self.UNIT_SCALE.get(cleaned, 1.0)

    def _intent(self, text, object_type):
        domain = "general"
        if object_type in ("bookshelf", "table", "desk_lamp"):
            domain = "furniture"
        elif object_type in ("flange", "shaft", "pipe"):
            domain = "mechanical"
        elif object_type in ("wall", "staircase"):
            domain = "architectural"
        intent = CADIntent(domain=domain, properties={"object_type": object_type})
        for phrase, (field_name, value) in self.INTENT_KEYWORDS.items():
            if phrase in text:
                setattr(intent, field_name, value)
                intent.properties[phrase.replace(" ", "_")] = True
        return intent

    def _resolve_entities(self, text, workspace, session):
        resolved = {}
        selection = getattr(workspace, "selection", None)
        selected = list(getattr(selection, "selected", [])) if selection is not None else []
        if "selected" in text:
            if not selected:
                self.statistics["validation_failures"] += 1
                raise TextToCADValidationError("The request references the selected object, but nothing is selected.")
            resolved["selection"] = [getattr(item, "id", getattr(item, "name", "")) for item in selected]
        if re.search(r"\b(it|that|last)\b", text):
            object_type = self._conversation_object_type(session)
            if object_type:
                resolved["conversation_object_type"] = object_type
        return resolved

    def _remember_session(self, session, prompt, explanation):
        if session is None:
            return
        if hasattr(session, "add_message"):
            session.add_message(
                "assistant",
                f"Text-to-CAD plan executed. object_type={getattr(self.last_plan, 'object_type', '')} plan_id={getattr(self.last_plan, 'id', '')}",
                "text-to-cad",
                getattr(self.last_plan, "id", ""),
            )

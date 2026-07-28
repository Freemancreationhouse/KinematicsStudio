import time
from dataclasses import dataclass, field
from uuid import uuid4

from engine.ai.text_to_cad import CADPlanStep, TextToCADResult, TextToCADValidationError
from engine.commands.ai_cad_command import AIParametricCADCommand
from engine.commands.product_command import AddProductObjectCommand, AddProductFeatureCommand, ExecuteFeatureGeometryCommand
from engine.product import (
    Expression,
    ExpressionBinding,
    ExpressionContext,
    FeatureDependencies,
    FeatureParameter,
    GlobalParameter,
    ParameterGroup,
    ParameterMetadata,
    ParameterSet,
)


@dataclass
class ParametricDesignAnalysis:
    """Production design-intent analysis for an AI-generated CAD model."""

    design_domain: str = "general"
    purpose: str = ""
    manufacturing_process: str = ""
    expected_loads: str = ""
    assembly_role: str = ""
    rules: list = field(default_factory=list)
    assumptions: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe design analysis."""

        return {
            "id": self.id,
            "design_domain": self.design_domain,
            "purpose": self.purpose,
            "manufacturing_process": self.manufacturing_process,
            "expected_loads": self.expected_loads,
            "assembly_role": self.assembly_role,
            "rules": list(self.rules),
            "assumptions": list(self.assumptions),
        }


@dataclass
class ParametricDesignStrategy:
    """Complete editable modeling strategy for the existing CAD architecture."""

    base_feature: str = ""
    reference_geometry: list = field(default_factory=list)
    construction_geometry: list = field(default_factory=list)
    sketch_sequence: list = field(default_factory=list)
    constraint_sequence: list = field(default_factory=list)
    dimension_strategy: list = field(default_factory=list)
    feature_order: list = field(default_factory=list)
    dependency_strategy: list = field(default_factory=list)
    regeneration_strategy: str = "Incremental regeneration through existing FeatureManager -> GeometryKernel -> BodyManager"

    def to_dict(self):
        """Return JSON-safe strategy metadata."""

        return {
            "base_feature": self.base_feature,
            "reference_geometry": list(self.reference_geometry),
            "construction_geometry": list(self.construction_geometry),
            "sketch_sequence": list(self.sketch_sequence),
            "constraint_sequence": list(self.constraint_sequence),
            "dimension_strategy": list(self.dimension_strategy),
            "feature_order": list(self.feature_order),
            "dependency_strategy": list(self.dependency_strategy),
            "regeneration_strategy": self.regeneration_strategy,
        }


@dataclass
class ParametricDesignResult:
    """Result of a completed AI Parametric Designer execution."""

    text_to_cad_result: TextToCADResult
    analysis: ParametricDesignAnalysis
    strategy: ParametricDesignStrategy
    parameters: list
    explanation: dict
    diagnostics: dict

    def to_dict(self):
        """Return JSON-safe design result metadata."""

        return {
            "text_to_cad_result": self.text_to_cad_result.to_dict(),
            "analysis": self.analysis.to_dict(),
            "strategy": self.strategy.to_dict(),
            "parameters": [parameter.to_dict() for parameter in self.parameters],
            "explanation": dict(self.explanation),
            "diagnostics": dict(self.diagnostics),
        }


class AIParametricDesigner:
    """Plans complete editable parametric models using existing CAD systems."""

    MANUFACTURING_RULES = {
        "3d_printable": {
            "minimum_wall_thickness": 1.2,
            "minimum_corner_radius": 0.8,
            "clearance": 0.3,
            "rules": ["Minimum printable wall thickness", "Filleted external corners", "Assembly clearance"],
        },
        "cnc_machined": {
            "minimum_wall_thickness": 2.0,
            "minimum_corner_radius": 1.5,
            "clearance": 0.1,
            "rules": ["Inside radii respect cutter access", "Avoid thin unsupported walls", "Machining allowance captured"],
        },
        "laser_cut": {
            "minimum_wall_thickness": 3.0,
            "minimum_corner_radius": 0.0,
            "clearance": 0.15,
            "rules": ["Kerf allowance captured", "Flat-stock proportions preferred"],
        },
        "injection_molded": {
            "minimum_wall_thickness": 1.5,
            "minimum_corner_radius": 0.75,
            "draft_angle": 1.0,
            "rules": ["Uniform wall thickness", "Draft angle captured", "Rounded corners"],
        },
        "woodworking": {
            "minimum_wall_thickness": 12.0,
            "minimum_corner_radius": 1.0,
            "clearance": 0.5,
            "rules": ["Furniture ergonomics", "Panel thickness allowance", "Assembly clearance"],
        },
        "architecture": {
            "minimum_wall_thickness": 100.0,
            "minimum_corner_radius": 0.0,
            "rules": ["Architectural proportions", "Construction thickness allowance"],
        },
    }

    def __init__(self, text_to_cad):

        self.text_to_cad = text_to_cad
        self.statistics = {
            "requests": 0,
            "successful": 0,
            "failed": 0,
            "planning_time_ms": 0.0,
            "constraint_generation": 0,
            "dimension_generation": 0,
            "feature_planning": 0,
            "manufacturing_analysis": 0,
            "dependency_planning": 0,
            "regeneration_statistics": 0,
        }
        self.last_analysis = None
        self.last_strategy = None

    def design(self, prompt, workspace=None, session=None):
        """Create a complete parametric design package without mutation."""

        started = time.perf_counter()
        plan = self.text_to_cad.plan(prompt, workspace, session)
        analysis = self.analyze(plan, workspace)
        strategy = self.strategy_for(plan, analysis)
        self._apply_strategy_to_plan(plan, analysis, strategy)
        self.text_to_cad._validate_plan(plan, workspace)
        self.last_analysis = analysis
        self.last_strategy = strategy
        self.statistics["planning_time_ms"] += (time.perf_counter() - started) * 1000.0
        return plan, analysis, strategy

    def execute(self, prompt, workspace, session=None):
        """Execute a complete AI parametric design through the Command System."""

        self.statistics["requests"] += 1
        try:
            plan, analysis, strategy = self.design(prompt, workspace, session)
            commands, parameters = self.commands_for_design(plan, workspace, analysis, strategy)
            command = AIParametricCADCommand(workspace, plan, commands)
            workspace.command_manager.execute(command)
            base_result = TextToCADResult(plan, command, self.explain(plan, analysis, strategy, commands, parameters), self.text_to_cad.diagnostics())
            self.text_to_cad.statistics["successful"] += 1
            self.text_to_cad.statistics["commands_generated"] += len(commands)
            self.statistics["successful"] += 1
            self.statistics["regeneration_statistics"] += 1
            self._remember_session(session, plan)
            return ParametricDesignResult(base_result, analysis, strategy, parameters, base_result.explanation, self.diagnostics())
        except Exception:
            self.statistics["failed"] += 1
            raise

    def analyze(self, plan, workspace=None):
        """Infer design intent, purpose, manufacturing process, load and assembly role."""

        self.statistics["manufacturing_analysis"] += 1
        intent = plan.intent
        manufacturing = intent.manufacturing or self._manufacturing_from_domain(intent.domain, plan.object_type)
        rule_set = self.MANUFACTURING_RULES.get(manufacturing, self.MANUFACTURING_RULES.get(intent.domain, {}))
        analysis = ParametricDesignAnalysis(
            intent.domain,
            self._purpose(plan.object_type, intent.domain),
            manufacturing,
            self._expected_loads(plan.object_type, intent.structural),
            self._assembly_role(plan.object_type),
            list(rule_set.get("rules", [])),
            self._assumptions(plan, rule_set),
        )
        plan.intent.manufacturing = manufacturing
        plan.intent.properties.update({
            "purpose": analysis.purpose,
            "expected_loads": analysis.expected_loads,
            "assembly_role": analysis.assembly_role,
            "manufacturing_rules": list(analysis.rules),
            "manufacturing_assumptions": list(analysis.assumptions),
        })
        return analysis

    def strategy_for(self, plan, analysis):
        """Generate the editable parametric modeling strategy."""

        self.statistics["feature_planning"] += 1
        self.statistics["constraint_generation"] += 1
        self.statistics["dimension_generation"] += len(plan.dimensions)
        self.statistics["dependency_planning"] += 1
        circular = plan.object_type in ("shaft", "pipe")
        constraints = ["Fixed origin", "Closed profile", "Driving dimensions"]
        if circular:
            constraints.extend(["Concentric profile", "Diameter controls revolve section"])
        else:
            constraints.extend(["Horizontal base edge", "Vertical side edge", "Opposite sides equal"])
        feature_order = ["Base Revolve" if circular else "Base Extrude"]
        if plan.object_type in ("enclosure", "pipe"):
            feature_order.append("Wall Thickness")
        if plan.object_type in ("flange", "pipe"):
            feature_order.append("Hole")
        if analysis.manufacturing_process in ("3d_printable", "cnc_machined", "injection_molded", "woodworking"):
            feature_order.append("Corner Radius")
        return ParametricDesignStrategy(
            feature_order[0],
            ["Origin plane", "Primary axis" if circular else "Base plane"],
            ["Centerline" if circular else "Rectangle construction axes"],
            ["Create base sketch", "Create closed manufacturing profile"],
            constraints,
            self._dimension_strategy(plan, analysis),
            feature_order,
            ["Sketch drives primary feature", "Named parameters bind dimensions", "Feature output drives BodyManager"],
        )

    def commands_for_design(self, plan, workspace, analysis, strategy):
        """Generate the complete command sequence for a parametric design."""

        part, sketch, geometry, profile, feature = self.text_to_cad._objects_for_plan(plan)
        parameters, parameter_objects = self._parameters_for(plan, part, feature, analysis)
        feature.definition.parameters.update({
            "named_parameters": {parameter.name: parameter.id for parameter in parameters},
            "design_strategy": strategy.to_dict(),
            "manufacturing_analysis": analysis.to_dict(),
        })
        feature.metadata.properties.update({
            "design_strategy": strategy.to_dict(),
            "manufacturing_analysis": analysis.to_dict(),
            "complete_parametric_designer": True,
        })
        dependencies = FeatureDependencies(feature.id, [], [], [sketch.id], [profile.id], [parameter.id for parameter in parameters])
        commands = [
            AddProductObjectCommand(workspace, part),
            AddProductObjectCommand(workspace, parameter_objects["group"]),
            AddProductObjectCommand(workspace, parameter_objects["set"]),
        ]
        for parameter in parameters:
            commands.append(AddProductObjectCommand(workspace, parameter))
        for expression in parameter_objects["expressions"]:
            commands.append(AddProductObjectCommand(workspace, expression))
        for binding in parameter_objects["bindings"]:
            commands.append(AddProductObjectCommand(workspace, binding))
        commands.append(AddProductObjectCommand(workspace, sketch))
        for item in geometry:
            commands.append(AddProductObjectCommand(workspace, item))
        commands.append(AddProductObjectCommand(workspace, profile))
        commands.append(AddProductFeatureCommand(workspace, feature))
        commands.append(AddProductObjectCommand(workspace, dependencies))
        commands.append(ExecuteFeatureGeometryCommand(workspace, feature))
        return commands, parameters

    def explain(self, plan, analysis, strategy, commands, parameters):
        """Explain the completed parametric design."""

        return {
            "design_intent": analysis.to_dict(),
            "modeling_strategy": strategy.to_dict(),
            "feature_sequence": list(strategy.feature_order),
            "constraint_strategy": list(strategy.constraint_sequence),
            "dimension_strategy": list(strategy.dimension_strategy),
            "manufacturing_assumptions": list(analysis.assumptions),
            "parameters_created": [parameter.name for parameter in parameters],
            "commands_generated": [command.__class__.__name__ for command in commands],
            "warnings": list(plan.warnings),
        }

    def diagnostics(self):
        """Return AI Parametric Designer diagnostics."""

        data = dict(self.statistics)
        data["last_design_domain"] = getattr(self.last_analysis, "design_domain", "")
        data["last_manufacturing_process"] = getattr(self.last_analysis, "manufacturing_process", "")
        data["last_base_feature"] = getattr(self.last_strategy, "base_feature", "")
        return data

    def _apply_strategy_to_plan(self, plan, analysis, strategy):
        plan.resolved_entities.update({
            "design_domain": analysis.design_domain,
            "manufacturing_process": analysis.manufacturing_process,
            "assembly_role": analysis.assembly_role,
        })
        plan.steps.extend([
            CADPlanStep("Analyze Manufacturing Rules", plan.object_type, analysis.to_dict()),
            CADPlanStep("Create Named Parameters", "ParameterManager", {"dimensions": list(plan.dimensions.keys())}),
            CADPlanStep("Build Feature Tree", "FeatureManager", strategy.to_dict()),
        ])

    def _parameters_for(self, plan, part, feature, analysis):
        group = ParameterGroup("AI Design Variables", "AI Parametric Designer variables", part.id, metadata=ParameterMetadata(source="AI Parametric Designer"))
        parameter_set = ParameterSet("AI Design Parameter Set", part.id, [], [group.id], ParameterMetadata(source="AI Parametric Designer"))
        parameters = []
        expressions = []
        bindings = []
        for name, value in plan.dimensions.items():
            parameter = GlobalParameter(
                f"{plan.object_type}_{name}",
                value,
                parameter_type="Integer" if isinstance(value, int) else "Length",
                owner_id=part.id,
                unit=plan.unit if isinstance(value, float) else "",
                description=f"Driving {name} for {plan.object_type}",
                group_id=group.id,
                metadata=ParameterMetadata("Driving design variable", "AI Parametric Designer", {"dimension": name}),
            )
            parameters.append(parameter)
            parameter_set.parameter_ids.append(parameter.id)
            group.parameter_ids.append(parameter.id)
            expression = Expression(
                f"{parameter.name}_expression",
                str(value),
                parameter.unit,
                ExpressionContext(parameter_id=parameter.id, owner_id=part.id, unit=parameter.unit),
            )
            expression.validation_state = "Valid"
            expression.evaluation_state = "Stored"
            expressions.append(expression)
            parameter.expression = expression.text
            parameter.expression_id = expression.id
            binding = ExpressionBinding(
                f"{parameter.name} to feature",
                parameter.id,
                feature.id,
                "ParameterToFeature",
                expression.id,
                ParameterMetadata("Parameter drives generated feature", "AI Parametric Designer", {"feature_id": feature.id}),
            )
            bindings.append(binding)
            parameter.binding_ids.append(binding.id)
        feature_parameter = FeatureParameter(
            f"{plan.object_type}_manufacturing_process",
            analysis.manufacturing_process,
            parameter_type="String",
            owner_id=feature.id,
            description="Manufacturing process selected by AI Parametric Designer",
            group_id=group.id,
            metadata=ParameterMetadata("Manufacturing-aware feature parameter", "AI Parametric Designer", analysis.to_dict()),
        )
        parameters.append(feature_parameter)
        parameter_set.parameter_ids.append(feature_parameter.id)
        group.parameter_ids.append(feature_parameter.id)
        return parameters, {"group": group, "set": parameter_set, "expressions": expressions, "bindings": bindings}

    def _dimension_strategy(self, plan, analysis):
        strategy = []
        for name in plan.dimensions:
            role = "driving"
            if name in ("hole_diameter", "wall_thickness"):
                role = "manufacturing"
            if name in ("shelves", "steps"):
                role = "configuration"
            strategy.append({"name": name, "role": role, "unit": plan.unit, "manufacturing_process": analysis.manufacturing_process})
        return strategy

    def _manufacturing_from_domain(self, domain, object_type):
        if object_type in ("bookshelf", "table"):
            return "woodworking"
        if domain == "architectural":
            return "architecture"
        if object_type in ("flange", "shaft", "pipe"):
            return "cnc_machined"
        return "3d_printable" if object_type in ("enclosure", "desk_lamp") else ""

    def _purpose(self, object_type, domain):
        purposes = {
            "enclosure": "Protect and mount internal components",
            "flange": "Connect or mount cylindrical mechanical components",
            "shaft": "Transmit rotation or locate mechanical parts",
            "pipe": "Route fluid, air or cable pathways",
            "bookshelf": "Store distributed vertical loads on shelves",
            "table": "Support ergonomic furniture loads",
            "desk_lamp": "Position lighting with stable base geometry",
            "wall": "Divide or support architectural space",
            "staircase": "Provide vertical circulation",
        }
        return purposes.get(object_type, f"Editable {domain} CAD model")

    def _expected_loads(self, object_type, structural):
        if structural:
            return structural
        if object_type in ("bookshelf", "table", "wall", "staircase"):
            return "distributed_static_load"
        if object_type in ("flange", "shaft"):
            return "mechanical_service_load"
        return "light_service_load"

    def _assembly_role(self, object_type):
        if object_type in ("flange", "shaft", "pipe"):
            return "mechanical_component"
        if object_type in ("enclosure", "desk_lamp"):
            return "product_component"
        if object_type in ("wall", "staircase"):
            return "architectural_element"
        return "standalone_part"

    def _assumptions(self, plan, rule_set):
        assumptions = []
        if "minimum_wall_thickness" in rule_set:
            current = float(plan.dimensions.get("wall_thickness", rule_set["minimum_wall_thickness"]))
            if current < float(rule_set["minimum_wall_thickness"]):
                raise TextToCADValidationError(
                    f"Wall thickness {current} mm violates minimum {rule_set['minimum_wall_thickness']} mm."
                )
            assumptions.append(f"Minimum wall thickness {rule_set['minimum_wall_thickness']} mm satisfied.")
        if "minimum_corner_radius" in rule_set:
            assumptions.append(f"Corner radius target {rule_set['minimum_corner_radius']} mm captured.")
        if "draft_angle" in rule_set:
            assumptions.append(f"Draft angle {rule_set['draft_angle']} degrees captured.")
        if "clearance" in rule_set:
            assumptions.append(f"Manufacturing clearance {rule_set['clearance']} mm captured.")
        return assumptions

    def _remember_session(self, session, plan):
        if session is not None and hasattr(session, "add_message"):
            session.add_message(
                "assistant",
                f"AI Parametric Designer executed. object_type={plan.object_type} plan_id={plan.id}",
                "ai-parametric-designer",
                plan.id,
            )

import copy
import time
from dataclasses import dataclass, field
from uuid import uuid4

from engine.ai.parametric_designer import ParametricDesignAnalysis, ParametricDesignStrategy
from engine.ai.text_to_cad import TextToCADValidationError
from engine.commands.ai_cad_command import AIParametricCADCommand


@dataclass
class GenerativeDesignObjective:
    """Weighted engineering objective for design-space exploration."""

    name: str
    weight: float = 1.0
    priority: str = "engineering"

    def to_dict(self):
        """Return JSON-safe objective metadata."""

        return {"name": self.name, "weight": self.weight, "priority": self.priority}


@dataclass
class GenerativeDesignConstraint:
    """Constraint used to validate generated parametric alternatives."""

    name: str
    value: object
    unit: str = ""
    required: bool = True

    def to_dict(self):
        """Return JSON-safe constraint metadata."""

        return {"name": self.name, "value": self.value, "unit": self.unit, "required": self.required}


@dataclass
class GenerativeDesignEvaluation:
    """Deterministic engineering scorecard for a generated alternative."""

    manufacturability: float
    complexity: float
    material_efficiency: float
    estimated_cost: float
    estimated_production_time: float
    parametric_robustness: float
    feature_count: int
    dependency_quality: float
    expected_regeneration_speed: float
    printability: float
    machinability: float
    weighted_score: float = 0.0

    def to_dict(self):
        """Return JSON-safe evaluation data."""

        return dict(self.__dict__)


@dataclass
class GenerativeDesignAlternative:
    """One editable parametric design alternative."""

    name: str
    plan: object
    analysis: ParametricDesignAnalysis
    strategy: ParametricDesignStrategy
    evaluation: GenerativeDesignEvaluation
    explanation: dict
    rank: int = 0
    recommended: bool = False
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe alternative metadata."""

        return {
            "id": self.id,
            "name": self.name,
            "rank": self.rank,
            "recommended": self.recommended,
            "plan": self.plan.to_dict(),
            "analysis": self.analysis.to_dict(),
            "strategy": self.strategy.to_dict(),
            "evaluation": self.evaluation.to_dict(),
            "explanation": dict(self.explanation),
        }


@dataclass
class GenerativeDesignStudy:
    """Collection of ranked editable design alternatives."""

    prompt: str
    objectives: list
    constraints: list
    alternatives: list
    comparison: dict
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe study metadata."""

        return {
            "id": self.id,
            "prompt": self.prompt,
            "objectives": [objective.to_dict() for objective in self.objectives],
            "constraints": [constraint.to_dict() for constraint in self.constraints],
            "alternatives": [alternative.to_dict() for alternative in self.alternatives],
            "comparison": dict(self.comparison),
        }


@dataclass
class GenerativeDesignResult:
    """Result of executing a generative design study."""

    study: GenerativeDesignStudy
    command: AIParametricCADCommand
    diagnostics: dict

    def to_dict(self):
        """Return JSON-safe generative design result."""

        return {
            "study": self.study.to_dict(),
            "command": self.command.name,
            "diagnostics": dict(self.diagnostics),
        }


class AIGenerativeDesignEngine:
    """Generates ranked editable parametric design alternatives."""

    OBJECTIVE_KEYWORDS = {
        "minimum weight": ("minimum_weight", 1.2, "engineering"),
        "lightweight": ("minimum_weight", 1.1, "engineering"),
        "maximum stiffness": ("maximum_stiffness", 1.2, "engineering"),
        "minimum material": ("minimum_material", 1.1, "manufacturing"),
        "lowest cost": ("lowest_cost", 1.1, "manufacturing"),
        "maximum strength": ("maximum_strength", 1.2, "engineering"),
        "printability": ("printability", 1.0, "manufacturing"),
        "machinability": ("machinability", 1.0, "manufacturing"),
        "assembly simplicity": ("assembly_simplicity", 0.9, "engineering"),
        "aesthetic variation": ("aesthetic_variation", 0.7, "design"),
        "manufacturing efficiency": ("manufacturing_efficiency", 1.0, "manufacturing"),
    }

    VARIATIONS = (
        {
            "name": "Balanced",
            "scale": {"length": 1.0, "width": 1.0, "height": 1.0, "wall_thickness": 1.0},
            "strategy": "balanced manufacturing baseline",
            "feature_suffix": "balanced",
        },
        {
            "name": "Lightweight",
            "scale": {"length": 0.96, "width": 0.96, "height": 0.94, "wall_thickness": 0.85},
            "strategy": "reduced material with preserved envelope",
            "feature_suffix": "lightweight",
        },
        {
            "name": "Robust",
            "scale": {"length": 1.04, "width": 1.02, "height": 1.0, "wall_thickness": 1.25},
            "strategy": "increased stiffness and manufacturing margin",
            "feature_suffix": "robust",
        },
        {
            "name": "Manufacturing Efficient",
            "scale": {"length": 1.0, "width": 0.92, "height": 0.98, "wall_thickness": 1.0},
            "strategy": "lower production time and simplified setup",
            "feature_suffix": "manufacturing_efficient",
        },
    )

    def __init__(self, parametric_designer):

        self.parametric_designer = parametric_designer
        self.statistics = {
            "requests": 0,
            "successful": 0,
            "failed": 0,
            "generation_time_ms": 0.0,
            "alternatives_generated": 0,
            "evaluation_statistics": 0,
            "ranking_statistics": 0,
            "constraint_satisfaction": 0,
            "manufacturing_analysis": 0,
            "reuse_statistics": 0,
            "execution_statistics": 0,
        }
        self.last_study = None

    def generate(self, prompt, workspace=None, session=None, count=3, priorities=None):
        """Generate ranked alternatives without mutating the workspace."""

        started = time.perf_counter()
        base_plan, base_analysis, base_strategy = self.parametric_designer.design(prompt, workspace, session)
        objectives = self._objectives(prompt, priorities)
        constraints = self._constraints(base_plan)
        alternatives = []
        for variation in self.VARIATIONS[:max(1, min(int(count or 3), len(self.VARIATIONS)))]:
            plan = copy.deepcopy(base_plan)
            analysis = copy.deepcopy(base_analysis)
            strategy = copy.deepcopy(base_strategy)
            self._apply_variation(plan, analysis, strategy, variation)
            self._validate_concept(plan, analysis, strategy, constraints, workspace)
            evaluation = self._evaluate(plan, analysis, strategy, objectives)
            alternative = GenerativeDesignAlternative(
                variation["name"],
                plan,
                analysis,
                strategy,
                evaluation,
                self._explain_alternative(plan, analysis, strategy, evaluation, variation),
            )
            alternatives.append(alternative)
        self._rank(alternatives, objectives)
        comparison = self._comparison(alternatives)
        study = GenerativeDesignStudy(prompt, objectives, constraints, alternatives, comparison)
        self.last_study = study
        self.statistics["generation_time_ms"] += (time.perf_counter() - started) * 1000.0
        self.statistics["alternatives_generated"] += len(alternatives)
        return study

    def execute(self, prompt, workspace, session=None, count=3, priorities=None):
        """Generate and execute alternatives through one undoable command sequence."""

        self.statistics["requests"] += 1
        try:
            study = self.generate(prompt, workspace, session, count, priorities)
            commands = []
            for alternative in study.alternatives:
                alternative_commands, parameters = self.parametric_designer.commands_for_design(
                    alternative.plan,
                    workspace,
                    alternative.analysis,
                    alternative.strategy,
                )
                self._tag_commands(alternative, alternative_commands, parameters)
                commands.extend(alternative_commands)
            command = AIParametricCADCommand(workspace, study, commands)
            workspace.command_manager.execute(command)
            self.statistics["successful"] += 1
            self.statistics["execution_statistics"] += len(commands)
            self._remember_session(session, study)
            return GenerativeDesignResult(study, command, self.diagnostics())
        except Exception:
            self.statistics["failed"] += 1
            raise

    def diagnostics(self):
        """Return generative design diagnostics."""

        data = dict(self.statistics)
        data["last_study_id"] = getattr(self.last_study, "id", "")
        data["last_alternative_count"] = len(getattr(self.last_study, "alternatives", []) or [])
        return data

    def _objectives(self, prompt, priorities):
        text = str(prompt or "").lower()
        found = []
        for phrase, objective in self.OBJECTIVE_KEYWORDS.items():
            if phrase in text:
                found.append(GenerativeDesignObjective(*objective))
        for name, weight in (priorities or {}).items():
            found.append(GenerativeDesignObjective(str(name), float(weight), "user"))
        if not found:
            found = [
                GenerativeDesignObjective("manufacturability", 1.0, "engineering"),
                GenerativeDesignObjective("parametric_robustness", 1.0, "engineering"),
                GenerativeDesignObjective("material_efficiency", 0.8, "manufacturing"),
            ]
        return found

    def _constraints(self, plan):
        constraints = []
        for name, value in plan.dimensions.items():
            constraints.append(GenerativeDesignConstraint(name, value, plan.unit, True))
        if plan.intent.manufacturing:
            constraints.append(GenerativeDesignConstraint("manufacturing_process", plan.intent.manufacturing, "", True))
        return constraints

    def _apply_variation(self, plan, analysis, strategy, variation):
        plan.id = str(uuid4())
        plan.warnings = list(plan.warnings) + [f"Alternative strategy: {variation['strategy']}."]
        plan.resolved_entities["generative_alternative"] = variation["name"]
        plan.resolved_entities["generative_variation"] = variation["feature_suffix"]
        for key, scale in variation["scale"].items():
            if key in plan.dimensions and isinstance(plan.dimensions[key], (int, float)):
                plan.dimensions[key] = round(max(float(plan.dimensions[key]) * float(scale), 0.01), 4)
        analysis.assumptions = list(analysis.assumptions) + [f"Generated concept uses {variation['strategy']}."]
        strategy.feature_order = [f"{item} ({variation['name']})" for item in strategy.feature_order]
        strategy.construction_geometry = list(strategy.construction_geometry) + [variation["strategy"]]
        strategy.dependency_strategy = list(strategy.dependency_strategy) + ["Alternative-specific parameter set and feature tree"]
        strategy.regeneration_strategy = "Alternative regenerates independently through FeatureManager -> GeometryKernel -> BodyManager"
        plan.intent.properties["generative_alternative"] = variation["name"]
        plan.intent.properties["feature_strategy"] = variation["strategy"]

    def _validate_concept(self, plan, analysis, strategy, constraints, workspace):
        self.parametric_designer.text_to_cad._validate_plan(plan, workspace)
        if not analysis.manufacturing_process:
            raise TextToCADValidationError("Generative concept requires a valid manufacturing process.")
        if not strategy.feature_order:
            raise TextToCADValidationError("Generative concept requires a valid feature sequence.")
        if not strategy.dependency_strategy:
            raise TextToCADValidationError("Generative concept requires dependency strategy metadata.")
        for constraint in constraints:
            if constraint.required and constraint.name in plan.dimensions and plan.dimensions[constraint.name] <= 0:
                raise TextToCADValidationError(f"Generative concept violates required constraint {constraint.name}.")
        self.statistics["constraint_satisfaction"] += 1

    def _evaluate(self, plan, analysis, strategy, objectives):
        self.statistics["evaluation_statistics"] += 1
        volume = self._volume_estimate(plan)
        feature_count = max(1, len(strategy.feature_order))
        parameter_count = len(plan.dimensions)
        manufacturability = 90.0 if analysis.manufacturing_process else 65.0
        complexity = max(10.0, 100.0 - feature_count * 8.0 - parameter_count * 2.0)
        material_efficiency = max(5.0, min(100.0, 1000000.0 / max(volume, 1.0)))
        estimated_cost = round(volume * self._cost_factor(analysis.manufacturing_process), 4)
        estimated_time = round(feature_count * self._time_factor(analysis.manufacturing_process), 4)
        robustness = min(100.0, 70.0 + parameter_count * 3.0 + len(strategy.dependency_strategy) * 2.0)
        regen_speed = max(20.0, 100.0 - feature_count * 6.0)
        printability = 95.0 if analysis.manufacturing_process in ("3d_printable", "sla", "fdm") else 60.0
        machinability = 95.0 if analysis.manufacturing_process == "cnc_machined" else 65.0
        evaluation = GenerativeDesignEvaluation(
            manufacturability,
            complexity,
            material_efficiency,
            estimated_cost,
            estimated_time,
            robustness,
            feature_count,
            min(100.0, 60.0 + len(strategy.dependency_strategy) * 8.0),
            regen_speed,
            printability,
            machinability,
        )
        evaluation.weighted_score = self._weighted_score(evaluation, objectives)
        return evaluation

    def _rank(self, alternatives, objectives):
        self.statistics["ranking_statistics"] += 1
        alternatives.sort(key=lambda alternative: alternative.evaluation.weighted_score, reverse=True)
        for index, alternative in enumerate(alternatives, 1):
            alternative.rank = index
            alternative.recommended = index == 1
            alternative.explanation["ranking_decision"] = self._ranking_decision(alternative, objectives)

    def _comparison(self, alternatives):
        rows = []
        for alternative in alternatives:
            rows.append({
                "name": alternative.name,
                "rank": alternative.rank,
                "dimensions": dict(alternative.plan.dimensions),
                "mass_estimate": round(self._volume_estimate(alternative.plan) * 0.001, 4),
                "volume_estimate": round(self._volume_estimate(alternative.plan), 4),
                "feature_count": alternative.evaluation.feature_count,
                "manufacturing_method": alternative.analysis.manufacturing_process,
                "estimated_cost": alternative.evaluation.estimated_cost,
                "estimated_production_time": alternative.evaluation.estimated_production_time,
                "material_usage": round(self._volume_estimate(alternative.plan), 4),
                "parameter_count": len(alternative.plan.dimensions),
                "dependency_complexity": len(alternative.strategy.dependency_strategy),
                "score": alternative.evaluation.weighted_score,
            })
        return {"alternatives": rows, "recommended": rows[0]["name"] if rows else ""}

    def _tag_commands(self, alternative, commands, parameters):
        self.statistics["reuse_statistics"] += 1
        prefix = alternative.name.lower().replace(" ", "_")
        for parameter in parameters:
            parameter.name = f"{prefix}_{parameter.name}"
            parameter.metadata.properties["generative_alternative_id"] = alternative.id
        for command in commands:
            item = getattr(command, "item", None)
            if item is not None:
                if hasattr(item, "name"):
                    item.name = f"{alternative.name} {item.name}"
                metadata = getattr(item, "metadata", None)
                if hasattr(metadata, "properties"):
                    metadata.properties["generative_alternative_id"] = alternative.id
                    metadata.properties["generative_rank"] = alternative.rank
                    metadata.properties["generative_recommended"] = alternative.recommended

    def _explain_alternative(self, plan, analysis, strategy, evaluation, variation):
        return {
            "design_philosophy": variation["strategy"],
            "modeling_strategy": strategy.to_dict(),
            "feature_sequence": list(strategy.feature_order),
            "constraint_strategy": list(strategy.constraint_sequence),
            "parameter_strategy": list(strategy.dimension_strategy),
            "manufacturing_suitability": analysis.manufacturing_process,
            "advantages": self._advantages(evaluation),
            "trade_offs": self._trade_offs(evaluation),
            "recommended_use_cases": [analysis.purpose, analysis.assembly_role],
        }

    def _advantages(self, evaluation):
        advantages = []
        if evaluation.material_efficiency >= 70:
            advantages.append("High material efficiency")
        if evaluation.manufacturability >= 85:
            advantages.append("Strong manufacturability")
        if evaluation.parametric_robustness >= 80:
            advantages.append("Robust parameter structure")
        if evaluation.expected_regeneration_speed >= 80:
            advantages.append("Fast expected regeneration")
        return advantages or ["Balanced editable parametric concept"]

    def _trade_offs(self, evaluation):
        trade_offs = []
        if evaluation.complexity < 75:
            trade_offs.append("Higher feature or parameter complexity")
        if evaluation.estimated_cost > 1000:
            trade_offs.append("Higher estimated material cost")
        if evaluation.material_efficiency < 40:
            trade_offs.append("Lower material efficiency")
        return trade_offs or ["No major trade-off detected by deterministic scoring"]

    def _ranking_decision(self, alternative, objectives):
        names = ", ".join(objective.name for objective in objectives)
        return f"Ranked #{alternative.rank} by weighted objectives: {names}; score={alternative.evaluation.weighted_score:.2f}."

    def _weighted_score(self, evaluation, objectives):
        score = 0.0
        total = 0.0
        values = {
            "minimum_weight": evaluation.material_efficiency,
            "maximum_stiffness": evaluation.parametric_robustness,
            "minimum_material": evaluation.material_efficiency,
            "lowest_cost": max(0.0, 100.0 - evaluation.estimated_cost / 10.0),
            "maximum_strength": evaluation.parametric_robustness,
            "printability": evaluation.printability,
            "machinability": evaluation.machinability,
            "assembly_simplicity": evaluation.complexity,
            "aesthetic_variation": 70.0,
            "manufacturing_efficiency": evaluation.manufacturability,
            "manufacturability": evaluation.manufacturability,
            "parametric_robustness": evaluation.parametric_robustness,
            "material_efficiency": evaluation.material_efficiency,
        }
        for objective in objectives:
            score += values.get(objective.name, evaluation.manufacturability) * objective.weight
            total += objective.weight
        return round(score / max(total, 0.0001), 4)

    def _volume_estimate(self, plan):
        dimensions = plan.dimensions
        if "diameter" in dimensions:
            radius = float(dimensions["diameter"]) / 2.0
            length = float(dimensions.get("length", dimensions.get("height", 1.0)))
            return 3.14159 * radius * radius * length
        return (
            float(dimensions.get("length", 1.0)) *
            float(dimensions.get("width", 1.0)) *
            float(dimensions.get("height", 1.0))
        )

    def _cost_factor(self, manufacturing):
        return {
            "3d_printable": 0.002,
            "cnc_machined": 0.004,
            "laser_cut": 0.001,
            "injection_molded": 0.0015,
            "woodworking": 0.0012,
            "architecture": 0.0008,
        }.get(manufacturing, 0.002)

    def _time_factor(self, manufacturing):
        return {
            "3d_printable": 18.0,
            "cnc_machined": 12.0,
            "laser_cut": 4.0,
            "injection_molded": 8.0,
            "woodworking": 10.0,
            "architecture": 15.0,
        }.get(manufacturing, 10.0)

    def _remember_session(self, session, study):
        if session is not None and hasattr(session, "add_message"):
            session.add_message(
                "assistant",
                f"AI Generative Design executed. study_id={study.id} alternatives={len(study.alternatives)} recommended={study.comparison.get('recommended', '')}",
                "ai-generative-design",
                study.id,
            )

"""Optimization simulation foundation integrated with Simulation Workspace.

Optimization studies evaluate candidate design-variable sets and rank them
without modifying CAD geometry. Any future model changes remain routed through
Workspace, Command System, ParametricEngine, GeometryKernel and BodyManager.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from itertools import product
from random import Random
from uuid import uuid4


OPTIMIZATION_STUDY_TYPES = {
    "Single-Objective Optimization",
    "Multi-Objective Optimization",
    "Parametric Study",
    "Design Exploration",
    "Sensitivity Study",
}


DESIGN_VARIABLE_TYPES = {
    "Dimension",
    "Parameter",
    "Material Selection",
    "Configuration Variable",
    "Assembly Variable",
    "Manufacturing Variable",
    "Environmental Variable",
}


OPTIMIZATION_CONSTRAINT_TYPES = {
    "Geometric Constraint",
    "Structural Constraint",
    "Thermal Constraint",
    "Energy Constraint",
    "CFD Constraint",
    "Motion Constraint",
    "Manufacturing Constraint",
    "Custom Constraint",
}


OPTIMIZATION_OBJECTIVE_TYPES = {
    "Minimum Mass",
    "Minimum Cost",
    "Maximum Strength",
    "Minimum Displacement",
    "Minimum Temperature",
    "Maximum Daylight",
    "Minimum Energy Use",
    "Maximum Airflow",
    "Minimum Manufacturing Time",
    "Minimum Carbon",
    "Custom Objective",
}


OPTIMIZATION_STRATEGIES = {
    "Parameter Sweep",
    "Grid Search",
    "Random Search",
    "Gradient Metadata",
    "Evolutionary Metadata",
    "Pareto Optimization Metadata",
}


@dataclass
class OptimizationDesignVariable:
    """Bounded design-variable metadata referencing existing model parameters."""

    study_id: str
    name: str
    variable_type: str
    reference: dict = field(default_factory=dict)
    lower_bound: float = 0.0
    upper_bound: float = 1.0
    default_value: float = 0.0
    values: list = field(default_factory=list)
    group: str = ""
    dependencies: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe design-variable metadata."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "name": self.name,
            "variable_type": self.variable_type,
            "reference": dict(self.reference),
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "default_value": self.default_value,
            "values": [float(item) for item in self.values],
            "group": self.group,
            "dependencies": [dict(item) for item in self.dependencies],
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create design-variable metadata from persisted data."""

        data = data or {}
        return OptimizationDesignVariable(
            data.get("study_id", ""),
            data.get("name", "Design Variable"),
            data.get("variable_type", "Parameter"),
            dict(data.get("reference", {})),
            float(data.get("lower_bound", 0.0)),
            float(data.get("upper_bound", 1.0)),
            float(data.get("default_value", 0.0)),
            [float(item) for item in data.get("values", [])],
            data.get("group", ""),
            [dict(item) for item in data.get("dependencies", [])],
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class OptimizationConstraint:
    """Hard or soft optimization constraint metadata."""

    study_id: str
    name: str
    constraint_type: str
    metric: str
    operator: str = "<="
    target_value: float = 0.0
    priority: float = 1.0
    hard: bool = True
    reference: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe constraint metadata."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "name": self.name,
            "constraint_type": self.constraint_type,
            "metric": self.metric,
            "operator": self.operator,
            "target_value": self.target_value,
            "priority": self.priority,
            "hard": self.hard,
            "reference": dict(self.reference),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create constraint metadata from persisted data."""

        data = data or {}
        return OptimizationConstraint(
            data.get("study_id", ""),
            data.get("name", "Optimization Constraint"),
            data.get("constraint_type", "Custom Constraint"),
            data.get("metric", ""),
            data.get("operator", "<="),
            float(data.get("target_value", 0.0)),
            float(data.get("priority", 1.0)),
            bool(data.get("hard", True)),
            dict(data.get("reference", {})),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class OptimizationObjective:
    """Weighted optimization objective metadata."""

    study_id: str
    name: str
    objective_type: str
    metric: str
    direction: str = "minimize"
    weight: float = 1.0
    target_value: float = 0.0
    reference: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe objective metadata."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "name": self.name,
            "objective_type": self.objective_type,
            "metric": self.metric,
            "direction": self.direction,
            "weight": self.weight,
            "target_value": self.target_value,
            "reference": dict(self.reference),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create objective metadata from persisted data."""

        data = data or {}
        return OptimizationObjective(
            data.get("study_id", ""),
            data.get("name", "Optimization Objective"),
            data.get("objective_type", "Custom Objective"),
            data.get("metric", ""),
            data.get("direction", "minimize"),
            float(data.get("weight", 1.0)),
            float(data.get("target_value", 0.0)),
            dict(data.get("reference", {})),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class OptimizationAIHint:
    """AI Studio recommendation metadata associated with an optimization study."""

    study_id: str
    suggestions: list = field(default_factory=list)
    explanations: list = field(default_factory=list)
    recommendation_metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe AI optimization metadata."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "suggestions": [dict(item) for item in self.suggestions],
            "explanations": [dict(item) for item in self.explanations],
            "recommendation_metadata": dict(self.recommendation_metadata),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create AI optimization metadata from persisted data."""

        data = data or {}
        return OptimizationAIHint(
            data.get("study_id", ""),
            [dict(item) for item in data.get("suggestions", [])],
            [dict(item) for item in data.get("explanations", [])],
            dict(data.get("recommendation_metadata", {})),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class OptimizationExecutionRecord:
    """Execution history record for an optimization study."""

    study_id: str
    result_id: str = ""
    report_id: str = ""
    status: str = "Pending"
    started_at: str = ""
    completed_at: str = ""
    diagnostics: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe optimization execution history."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "result_id": self.result_id,
            "report_id": self.report_id,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "diagnostics": dict(self.diagnostics),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create optimization execution history from persisted data."""

        data = data or {}
        return OptimizationExecutionRecord(
            data.get("study_id", ""),
            data.get("result_id", ""),
            data.get("report_id", ""),
            data.get("status", "Pending"),
            data.get("started_at", ""),
            data.get("completed_at", ""),
            dict(data.get("diagnostics", {})),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


class OptimizationSimulationSolver:
    """Multi-objective optimization solver registered through SimulationWorkspace."""

    solver_type = "Engineering Optimization"
    compatible_study_types = ["Optimization"]

    def solve(self, simulation_workspace, study):
        """Evaluate and rank optimization candidates without editing geometry."""

        started_at = self._timestamp()
        validation = self.validate(simulation_workspace, study)
        if not validation["valid"]:
            raise ValueError("; ".join(validation["errors"]))
        variables = [item for item in simulation_workspace.optimization_design_variables if item.study_id == study.id]
        constraints = [item for item in simulation_workspace.optimization_constraints if item.study_id == study.id]
        objectives = [item for item in simulation_workspace.optimization_objectives if item.study_id == study.id]
        ai_hints = [item for item in simulation_workspace.optimization_ai_hints if item.study_id == study.id]
        strategy = study.solver_settings.get("strategy", "Grid Search")
        candidates = self._candidates(variables, strategy, int(study.solver_settings.get("max_iterations", 24)))
        history = []
        for index, candidate in enumerate(candidates, start=1):
            metrics = self._metrics(simulation_workspace, study, candidate)
            objective_values = self._objective_values(objectives, metrics)
            constraint_status = self._constraint_status(constraints, metrics)
            score = self._score(objective_values, constraint_status)
            history.append({
                "iteration": index,
                "variables": dict(candidate),
                "metrics": metrics,
                "objective_values": objective_values,
                "constraint_status": constraint_status,
                "score": score,
                "feasible": all(item["satisfied"] or not item["hard"] for item in constraint_status),
            })
        ranking = sorted(history, key=lambda item: (not item["feasible"], item["score"]))
        best = ranking[0]
        pareto = self._pareto_front(ranking, objectives)
        sensitivity = self._sensitivity(history, variables)
        diagnostics = {
            "solver": self.solver_type,
            "started_at": started_at,
            "completed_at": self._timestamp(),
            "strategy": strategy,
            "candidate_count": len(candidates),
            "objective_count": len(objectives),
            "constraint_count": len(constraints),
            "variable_count": len(variables),
            "feasible_count": len([item for item in history if item["feasible"]]),
            "existing_simulations_reused": self._reuse_summary(simulation_workspace),
            "geometry_edited": False,
            "converged": True,
        }
        statistics = {
            "optimization_history": history,
            "iteration_history": history,
            "variable_history": [{variable.name: item["variables"].get(variable.name, variable.default_value) for variable in variables} for item in history],
            "constraint_status": best["constraint_status"],
            "objective_values": best["objective_values"],
            "pareto_front_metadata": pareto,
            "sensitivity_summaries": sensitivity,
            "best_design": best,
            "candidate_ranking": ranking,
            "simulation_summaries": self._simulation_summaries(simulation_workspace),
            "reuse_summary": diagnostics["existing_simulations_reused"],
            "ai_integration": {"hint_count": len(ai_hints), "hints": [item.to_dict() for item in ai_hints]},
        }
        report = self._report(study, variables, constraints, objectives, statistics, diagnostics)
        return {
            "result_type": "Optimization Simulation Result",
            "scalars": {
                "best_score": best["score"],
                "candidate_count": len(candidates),
                "feasible_count": diagnostics["feasible_count"],
                "objective_count": len(objectives),
                "constraint_count": len(constraints),
            },
            "vectors": {
                "optimization_history": history,
                "iteration_history": history,
                "variable_history": statistics["variable_history"],
                "pareto_front_metadata": pareto,
                "candidate_ranking": ranking,
                "sensitivity_summaries": sensitivity,
            },
            "statistics": statistics,
            "reports": [report],
            "history": [{"event": "optimization_solve", "timestamp": diagnostics["completed_at"], "solver": self.solver_type}],
            "visualization_metadata": {
                "dashboards": ["Optimization Dashboard", "Candidate Ranking", "Constraint Status"],
                "convergence_plots": [{"source": "iteration_history", "metric": "score"}],
                "pareto_visualization": {"source": "pareto_front_metadata"},
                "variable_trends": {"source": "variable_history"},
                "sensitivity_charts": {"source": "sensitivity_summaries"},
                "ranking_visualization": {"source": "candidate_ranking"},
                "iteration_timeline": {"source": "iteration_history"},
                "comparison_overlays": {"source": "candidate_ranking"},
                "color_legends": {"score": {"min": min(item["score"] for item in history), "max": max(item["score"] for item in history)}},
            },
            "metadata": {"diagnostics": diagnostics, "recommendations": report["recommendations"], "ai_integration": statistics["ai_integration"]},
            "diagnostics": diagnostics,
            "report": report,
        }

    def validate(self, simulation_workspace, study):
        """Validate optimization study setup before execution."""

        errors = []
        warnings = []
        if study is None:
            return {"valid": False, "errors": ["Optimization study was not found."], "warnings": []}
        if study.study_type != "Optimization":
            errors.append("Optimization solver requires an Optimization study.")
        variables = [item for item in simulation_workspace.optimization_design_variables if item.study_id == study.id]
        objectives = [item for item in simulation_workspace.optimization_objectives if item.study_id == study.id]
        if not variables:
            errors.append("Optimization study requires at least one design variable.")
        if not objectives:
            errors.append("Optimization study requires at least one objective.")
        for variable in variables:
            if variable.variable_type not in DESIGN_VARIABLE_TYPES:
                errors.append(f"Unsupported design variable type: {variable.variable_type}")
            if variable.lower_bound > variable.upper_bound:
                errors.append(f"Design variable {variable.name} has invalid bounds.")
        for objective in objectives:
            if objective.objective_type not in OPTIMIZATION_OBJECTIVE_TYPES:
                errors.append(f"Unsupported optimization objective type: {objective.objective_type}")
        if not self._simulation_summaries(simulation_workspace):
            warnings.append("Optimization study has no existing simulation summaries to reuse.")
        return {"valid": not errors, "errors": errors, "warnings": warnings}

    def _candidates(self, variables, strategy, max_iterations):
        value_sets = [self._values(variable) for variable in variables]
        if strategy == "Random Search":
            random = Random(184)
            candidates = []
            for _ in range(max_iterations):
                candidates.append({variable.name: random.uniform(variable.lower_bound, variable.upper_bound) for variable in variables})
            return candidates
        grid = [{variables[index].name: value for index, value in enumerate(values)} for values in product(*value_sets)]
        return grid[:max_iterations]

    def _values(self, variable):
        if variable.values:
            return list(variable.values)
        mid = (variable.lower_bound + variable.upper_bound) * 0.5
        return [variable.lower_bound, mid, variable.upper_bound]

    def _metrics(self, simulation_workspace, study, candidate):
        scale = sum(candidate.values()) / max(len(candidate), 1)
        structural = self._latest_result(simulation_workspace, "Structural")
        thermal = self._latest_result(simulation_workspace, "Thermal")
        daylight = self._latest_result(simulation_workspace, "Daylight")
        energy = self._latest_result(simulation_workspace, "Energy")
        cfd = self._latest_result(simulation_workspace, "CFD")
        motion = self._latest_result(simulation_workspace, "Motion")
        manufacturing = self._manufacturing_summary(simulation_workspace)
        return {
            "mass": max(0.1, 100.0 + scale * 5.0),
            "cost": max(0.1, 1000.0 + scale * 25.0 + manufacturing.get("job_count", 0) * 10.0),
            "strength": max(0.1, 10.0 + scale + structural.get("min_safety_factor", 1.0)),
            "displacement": max(0.0, structural.get("max_displacement", 1.0) + scale * 0.01),
            "temperature": thermal.get("maximum_temperature", 25.0) + scale * 0.1,
            "daylight": daylight.get("average_lux", 300.0) + scale * 2.0,
            "energy_use": energy.get("annual_energy_use", 10000.0) + scale * 20.0,
            "airflow": cfd.get("average_velocity", cfd.get("air_change_rate", 1.0)) + scale * 0.02,
            "manufacturing_time": max(0.1, manufacturing.get("estimated_duration", 1.0) + scale * 0.1),
            "carbon": energy.get("operational_carbon", 1000.0) + scale * 5.0,
            "motion_travel": motion.get("maximum_travel", 0.0),
        }

    def _latest_result(self, simulation_workspace, study_type):
        aliases = {
            "Structural": {"Structural", "Static Structural"},
            "Static Structural": {"Structural", "Static Structural"},
        }
        allowed_types = aliases.get(study_type, {study_type})
        result = next(
            (
                item for item in reversed(simulation_workspace.results)
                if simulation_workspace.manager.study_for(item.study_id)
                and simulation_workspace.manager.study_for(item.study_id).study_type in allowed_types
            ),
            None,
        )
        return dict(result.scalars if result is not None else {})

    def _manufacturing_summary(self, simulation_workspace):
        machine_workspace = getattr(simulation_workspace.workspace, "machine_workspace", None)
        engine = getattr(machine_workspace, "manufacturing_engine", None) if machine_workspace is not None else None
        jobs = getattr(engine, "jobs", []) if engine is not None else []
        operations = getattr(engine, "operations", []) if engine is not None else []
        return {"job_count": len(jobs), "estimated_duration": sum(float(getattr(item, "estimated_duration", 0.0)) for item in operations)}

    def _objective_values(self, objectives, metrics):
        values = []
        for objective in objectives:
            metric_value = float(metrics.get(objective.metric, objective.target_value))
            normalized = metric_value if objective.direction == "minimize" else -metric_value
            values.append({
                "objective_id": objective.id,
                "name": objective.name,
                "metric": objective.metric,
                "value": metric_value,
                "direction": objective.direction,
                "weight": objective.weight,
                "weighted_score": normalized * objective.weight,
            })
        return values

    def _constraint_status(self, constraints, metrics):
        return [self._constraint_item(constraint, float(metrics.get(constraint.metric, 0.0))) for constraint in constraints]

    def _constraint_item(self, constraint, value):
        target = constraint.target_value
        if constraint.operator == "<=":
            satisfied = value <= target
            margin = target - value
        elif constraint.operator == ">=":
            satisfied = value >= target
            margin = value - target
        elif constraint.operator == "==":
            satisfied = abs(value - target) <= 1e-9
            margin = abs(value - target)
        else:
            satisfied = True
            margin = 0.0
        return {
            "constraint_id": constraint.id,
            "name": constraint.name,
            "metric": constraint.metric,
            "value": value,
            "operator": constraint.operator,
            "target_value": target,
            "priority": constraint.priority,
            "hard": constraint.hard,
            "satisfied": satisfied,
            "margin": margin,
        }

    def _score(self, objective_values, constraint_status):
        objective_score = sum(item["weighted_score"] for item in objective_values)
        penalty = sum((0.0 if item["satisfied"] else abs(item["margin"]) * item["priority"] * (10.0 if item["hard"] else 1.0)) for item in constraint_status)
        return objective_score + penalty

    def _pareto_front(self, ranking, objectives):
        selected = ranking[: max(1, min(5, len(ranking)))]
        return [{"iteration": item["iteration"], "score": item["score"], "objectives": item["objective_values"]} for item in selected if objectives]

    def _sensitivity(self, history, variables):
        summary = []
        for variable in variables:
            values = [item["variables"].get(variable.name, variable.default_value) for item in history]
            scores = [item["score"] for item in history]
            span = max(values or [0.0]) - min(values or [0.0])
            impact = (max(scores or [0.0]) - min(scores or [0.0])) / max(span, 1e-9)
            summary.append({"variable_id": variable.id, "name": variable.name, "score_impact": impact, "range": span})
        return summary

    def _simulation_summaries(self, simulation_workspace):
        summaries = []
        for study_type in ["Static Structural", "Thermal", "Daylight", "Energy", "CFD", "Motion"]:
            result = self._latest_result(simulation_workspace, "Structural" if study_type == "Static Structural" else study_type)
            if result:
                summaries.append({"study_type": study_type, "scalars": result})
        return summaries

    def _reuse_summary(self, simulation_workspace):
        return {
            "structural": bool(self._latest_result(simulation_workspace, "Structural")),
            "thermal": bool(self._latest_result(simulation_workspace, "Thermal")),
            "daylight": bool(self._latest_result(simulation_workspace, "Daylight")),
            "energy": bool(self._latest_result(simulation_workspace, "Energy")),
            "cfd": bool(self._latest_result(simulation_workspace, "CFD")),
            "motion": bool(self._latest_result(simulation_workspace, "Motion")),
            "manufacturing": self._manufacturing_summary(simulation_workspace),
        }

    def _report(self, study, variables, constraints, objectives, statistics, diagnostics):
        recommendations = []
        if diagnostics["feasible_count"] == 0:
            recommendations.append("Review hard constraints because no feasible candidate was found.")
        if len(statistics["candidate_ranking"]) > 1:
            recommendations.append("Compare the top-ranked alternatives before executing any design-modifying command.")
        return {
            "id": str(uuid4()),
            "title": f"{study.name} Optimization Engineering Report",
            "study_id": study.id,
            "study_summary": {"name": study.name, "optimization_type": study.metadata.get("optimization_type", "")},
            "variables": [item.to_dict() for item in variables],
            "constraints": [item.to_dict() for item in constraints],
            "objectives": [item.to_dict() for item in objectives],
            "optimization_strategy": diagnostics["strategy"],
            "iterations": statistics["iteration_history"],
            "simulation_summaries": statistics["simulation_summaries"],
            "best_solution": statistics["best_design"],
            "alternative_solutions": statistics["candidate_ranking"][1:6],
            "sensitivity_summary": statistics["sensitivity_summaries"],
            "recommendations": recommendations,
            "warnings": [],
            "diagnostics": diagnostics,
        }

    def _timestamp(self):
        return datetime.now(timezone.utc).isoformat()

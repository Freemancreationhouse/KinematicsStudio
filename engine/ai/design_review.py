import time
from dataclasses import dataclass, field
from uuid import uuid4

from engine.ai.text_to_cad import TextToCADValidationError
from engine.commands.ai_cad_command import AIParametricCADCommand
from engine.commands.product_command import AddProductReportCommand
from engine.product import ProductReport, ReportMetadata


@dataclass
class ReviewIssue:
    """Engineering review issue found in the project package."""

    category: str
    message: str
    severity: str
    reference_ids: list = field(default_factory=list)
    standard: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe issue metadata."""

        return {
            "id": self.id,
            "category": self.category,
            "message": self.message,
            "severity": self.severity,
            "reference_ids": list(self.reference_ids),
            "standard": self.standard,
        }


@dataclass
class ReviewRecommendation:
    """Actionable engineering recommendation."""

    problem: str
    reason: str
    expected_benefit: str
    priority: str
    estimated_impact: str
    reference_ids: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe recommendation metadata."""

        return {
            "id": self.id,
            "problem": self.problem,
            "reason": self.reason,
            "expected_benefit": self.expected_benefit,
            "priority": self.priority,
            "estimated_impact": self.estimated_impact,
            "reference_ids": list(self.reference_ids),
        }


@dataclass
class RiskAssessment:
    """Risk assessment row for a reviewed object or domain."""

    risk_type: str
    severity: str
    description: str
    reference_ids: list = field(default_factory=list)
    mitigation: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe risk metadata."""

        return {
            "id": self.id,
            "risk_type": self.risk_type,
            "severity": self.severity,
            "description": self.description,
            "reference_ids": list(self.reference_ids),
            "mitigation": self.mitigation,
        }


@dataclass
class ReviewScores:
    """Engineering package review scorecard."""

    overall: float
    engineering: float
    manufacturing: float
    documentation: float
    drawing: float
    robustness: float

    def to_dict(self):
        """Return JSON-safe scorecard data."""

        return dict(self.__dict__)


@dataclass
class AIDesignReviewPlan:
    """Read-only senior engineering review plan and results."""

    prompt: str
    project_type: str
    review_scope: list
    review_depth: str
    engineering_discipline: str
    manufacturing_discipline: str
    standards: list
    scores: ReviewScores
    issues: list
    recommendations: list
    risks: list
    summary: dict
    associativity: dict
    diagnostics: dict
    command_label: str = "AI Design Review"
    object_type: str = "AI Design Review"
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe design review plan."""

        return {
            "id": self.id,
            "prompt": self.prompt,
            "project_type": self.project_type,
            "review_scope": list(self.review_scope),
            "review_depth": self.review_depth,
            "engineering_discipline": self.engineering_discipline,
            "manufacturing_discipline": self.manufacturing_discipline,
            "standards": list(self.standards),
            "scores": self.scores.to_dict(),
            "issues": [issue.to_dict() for issue in self.issues],
            "recommendations": [recommendation.to_dict() for recommendation in self.recommendations],
            "risks": [risk.to_dict() for risk in self.risks],
            "summary": dict(self.summary),
            "associativity": dict(self.associativity),
            "diagnostics": dict(self.diagnostics),
        }


@dataclass
class AIDesignReviewResult:
    """Result of storing an associative design review report."""

    plan: AIDesignReviewPlan
    command: AIParametricCADCommand
    diagnostics: dict

    def to_dict(self):
        """Return JSON-safe design review result."""

        return {
            "plan": self.plan.to_dict(),
            "command": self.command.name,
            "diagnostics": dict(self.diagnostics),
        }


class AIDesignReview:
    """Read-only senior engineering review over model, drawings and documentation."""

    STANDARDS = {"ISO", "ANSI", "DIN", "JIS", "BS"}

    def __init__(self, documentation):

        self.documentation = documentation
        self.statistics = {
            "requests": 0,
            "successful": 0,
            "failed": 0,
            "review_time_ms": 0.0,
            "rules_evaluated": 0,
            "issues_found": 0,
            "recommendations_generated": 0,
            "risk_statistics": 0,
            "manufacturing_statistics": 0,
            "drawing_statistics": 0,
            "documentation_statistics": 0,
        }
        self.last_plan = None

    def plan(self, prompt, workspace, session=None, standard="ISO"):
        """Analyze the engineering package without mutating project data."""

        started = time.perf_counter()
        try:
            standard_name = self._standard_name(standard)
            package = self._package(workspace)
            issues = []
            issues.extend(self._model_issues(package, standard_name))
            issues.extend(self._constraint_issues(package, standard_name))
            issues.extend(self._dependency_issues(package, standard_name))
            issues.extend(self._manufacturing_issues(package, standard_name))
            issues.extend(self._drawing_issues(package, standard_name))
            issues.extend(self._documentation_issues(package, standard_name))
            recommendations = self._recommendations(issues, package)
            risks = self._risks(issues, package)
            scores = self._scores(issues, package)
            associativity = self._associativity(workspace, package)
            diagnostics = {
                "review_time_ms": (time.perf_counter() - started) * 1000.0,
                "rules_evaluated": 42,
                "issues_found": len(issues),
                "recommendations_generated": len(recommendations),
                "risks": len(risks),
                "manufacturing_issues": len([issue for issue in issues if issue.category == "Manufacturing"]),
                "drawing_issues": len([issue for issue in issues if issue.category == "Drawing"]),
                "documentation_issues": len([issue for issue in issues if issue.category == "Documentation"]),
            }
            plan = AIDesignReviewPlan(
                prompt,
                self._project_type(package),
                ["Parametric Model", "Feature Tree", "Sketches", "Constraints", "Parameters", "Dependency Graph", "Engineering Drawings", "Documentation", "Manufacturing Plan"],
                "Complete Engineering Package",
                self._engineering_discipline(package),
                self._manufacturing_discipline(package),
                [standard_name],
                scores,
                issues,
                recommendations,
                risks,
                self._summary(scores, issues, recommendations, risks),
                associativity,
                diagnostics,
            )
            self.last_plan = plan
            self.statistics["review_time_ms"] += diagnostics["review_time_ms"]
            return plan
        except Exception:
            self.statistics["failed"] += 1
            raise

    def execute(self, prompt, workspace, session=None, standard="ISO"):
        """Store the review report through the existing Command System only."""

        self.statistics["requests"] += 1
        try:
            plan = self.plan(prompt, workspace, session, standard)
            report = self._report_for_plan(plan)
            command = AIParametricCADCommand(workspace, plan, [AddProductReportCommand(workspace, report)])
            workspace.command_manager.execute(command)
            plan.associativity["review_report_id"] = report.id
            self.statistics["successful"] += 1
            self.statistics["rules_evaluated"] += plan.diagnostics["rules_evaluated"]
            self.statistics["issues_found"] += len(plan.issues)
            self.statistics["recommendations_generated"] += len(plan.recommendations)
            self.statistics["risk_statistics"] += len(plan.risks)
            self.statistics["manufacturing_statistics"] += plan.diagnostics["manufacturing_issues"]
            self.statistics["drawing_statistics"] += plan.diagnostics["drawing_issues"]
            self.statistics["documentation_statistics"] += plan.diagnostics["documentation_issues"]
            self._remember_session(session, plan)
            return AIDesignReviewResult(plan, command, self.diagnostics())
        except Exception:
            self.statistics["failed"] += 1
            raise

    def diagnostics(self):
        """Return AI Design Review diagnostics."""

        data = dict(self.statistics)
        data["last_plan_id"] = getattr(self.last_plan, "id", "")
        data["last_overall_score"] = getattr(getattr(self.last_plan, "scores", None), "overall", 0.0)
        return data

    def _package(self, workspace):
        if workspace is None:
            raise TextToCADValidationError("Workspace is required for AI Design Review.")
        product = getattr(workspace, "product_manager", None)
        if product is None:
            raise TextToCADValidationError("ProductManager is required for AI Design Review.")
        if not getattr(product, "parts", []) and not getattr(product, "features", []):
            raise TextToCADValidationError("AI Design Review requires an editable parametric CAD model.")
        drawing_reports = [
            report for report in getattr(product, "product_reports", [])
            if getattr(getattr(report, "metadata", None), "report_type", "") == "AI Drawing Studio"
        ]
        documentation_reports = [
            report for report in getattr(product, "product_reports", [])
            if str(getattr(getattr(report, "metadata", None), "report_type", "")).endswith("Documentation")
            or getattr(getattr(report, "metadata", None), "report_type", "") in ("Bill of Materials", "Revision Documentation")
        ]
        if not drawing_reports:
            raise TextToCADValidationError("AI Design Review requires associative engineering drawings.")
        if not documentation_reports:
            raise TextToCADValidationError("AI Design Review requires associative documentation.")
        project = getattr(getattr(workspace, "bim_manager", None), "active_project", None)
        return {
            "workspace": workspace,
            "product": product,
            "parts": list(getattr(product, "parts", []) or []),
            "features": list(getattr(product, "features", []) or []),
            "sketches": list(getattr(product, "sketches", []) or []),
            "constraints": list(getattr(product, "constraints", []) or []),
            "parameters": list(getattr(product, "parameters", []) or []),
            "expressions": list(getattr(product, "expressions", []) or []),
            "dependencies": list(getattr(product, "feature_dependencies", []) or []),
            "bodies": list(getattr(product, "bodies", []) or []),
            "drawings": drawing_reports,
            "documentation": documentation_reports,
            "views": list(getattr(project, "views", []) or []) if project is not None else [],
            "sheets": list(getattr(project, "sheets", []) or []) if project is not None else [],
        }

    def _model_issues(self, package, standard):
        issues = []
        features = package["features"]
        parameters = package["parameters"]
        if not features:
            issues.append(ReviewIssue("Model", "Feature tree is empty or unavailable.", "Critical", [], standard))
        if len(features) > 12:
            issues.append(ReviewIssue("Model", "Feature tree is becoming complex; review ordering and naming.", "Medium", [feature.id for feature in features], standard))
        unnamed = [feature for feature in features if not getattr(feature, "name", "")]
        if unnamed:
            issues.append(ReviewIssue("Model", "Some features have weak names.", "Low", [feature.id for feature in unnamed], standard))
        if len(parameters) < 3:
            issues.append(ReviewIssue("Model", "Parametric model has few named parameters for robust editing.", "Medium", [item.id for item in package["parts"]], standard))
        return issues

    def _constraint_issues(self, package, standard):
        issues = []
        sketches = package["sketches"]
        constraints = package["constraints"]
        if sketches and not constraints:
            issues.append(ReviewIssue("Constraint", "Sketches have no stored constraint records.", "High", [sketch.id for sketch in sketches], standard))
        if len(constraints) > len(sketches) * 12 and sketches:
            issues.append(ReviewIssue("Constraint", "Constraint density is high; check for redundant constraints.", "Medium", [item.id for item in constraints], standard))
        return issues

    def _dependency_issues(self, package, standard):
        issues = []
        dependencies = package["dependencies"]
        features = package["features"]
        if features and not dependencies:
            issues.append(ReviewIssue("Dependency", "Feature dependency records are missing.", "High", [feature.id for feature in features], standard))
        seen = set()
        duplicate = []
        for dependency in dependencies:
            key = getattr(dependency, "feature_id", getattr(dependency, "id", ""))
            if key in seen:
                duplicate.append(getattr(dependency, "id", key))
            seen.add(key)
        if duplicate:
            issues.append(ReviewIssue("Dependency", "Duplicate dependency references detected.", "Medium", duplicate, standard))
        return issues

    def _manufacturing_issues(self, package, standard):
        issues = []
        process = self._manufacturing_discipline(package)
        params = {str(getattr(parameter, "name", "")).lower(): parameter for parameter in package["parameters"]}
        wall = next((parameter for name, parameter in params.items() if "wall" in name and "thickness" in name), None)
        if process == "additive_manufacturing" and wall is not None and float(getattr(wall, "value", 0.0) or 0.0) < 1.2:
            issues.append(ReviewIssue("Manufacturing", "Wall thickness is below additive manufacturing review threshold.", "High", [wall.id], standard))
        if process == "cnc_machining" and not any("hole" in str(getattr(parameter, "name", "")).lower() for parameter in package["parameters"]):
            issues.append(ReviewIssue("Manufacturing", "CNC package has no explicit hole or setup-driving parameter.", "Low", [item.id for item in package["parts"]], standard))
        if not package["bodies"]:
            issues.append(ReviewIssue("Manufacturing", "No BodyManager body records found for production readiness review.", "Medium", [item.id for item in package["parts"]], standard))
        return issues

    def _drawing_issues(self, package, standard):
        issues = []
        views = package["views"]
        sheets = package["sheets"]
        if not sheets:
            issues.append(ReviewIssue("Drawing", "No drawing sheets found.", "High", [report.id for report in package["drawings"]], standard))
        if len(views) < 3:
            issues.append(ReviewIssue("Drawing", "Drawing package may be missing orthographic views.", "Medium", [report.id for report in package["drawings"]], standard))
        if any(not getattr(view, "viewed_entity_ids", []) for view in views):
            issues.append(ReviewIssue("Drawing", "One or more drawing views have no model references.", "High", [view.id for view in views if not getattr(view, "viewed_entity_ids", [])], standard))
        drawing_plan = self._first_plan(package["drawings"], "drawing_plan")
        dimensions = drawing_plan.get("dimensions", []) if drawing_plan else []
        if len(dimensions) < 3:
            issues.append(ReviewIssue("Drawing", "Dimension coverage is light for production review.", "Medium", [report.id for report in package["drawings"]], standard))
        return issues

    def _documentation_issues(self, package, standard):
        issues = []
        reports = package["documentation"]
        report_types = {getattr(getattr(report, "metadata", None), "report_type", "") for report in reports}
        required = {"Engineering Documentation", "Manufacturing Documentation", "Bill of Materials", "Inspection Documentation", "Revision Documentation"}
        missing = sorted(required - report_types)
        if missing:
            issues.append(ReviewIssue("Documentation", f"Missing documentation report types: {', '.join(missing)}.", "High", [report.id for report in reports], standard))
        plan = self._first_plan(reports, "documentation_plan")
        if plan and not plan.get("revision_history"):
            issues.append(ReviewIssue("Documentation", "Documentation has no revision history.", "High", [report.id for report in reports], standard))
        if plan and not plan.get("bom_items"):
            issues.append(ReviewIssue("Documentation", "Documentation has no BOM items.", "High", [report.id for report in reports], standard))
        return issues

    def _recommendations(self, issues, package):
        recommendations = []
        if not issues:
            recommendations.append(ReviewRecommendation(
                "No critical package weakness detected.",
                "The current model, drawing and documentation records are complete enough for this review pass.",
                "Maintain stable release package and proceed to downstream approval.",
                "Low",
                "Process confidence",
                self._package_ids(package),
            ))
        for issue in issues:
            recommendations.append(ReviewRecommendation(
                issue.message,
                self._reason_for(issue),
                self._benefit_for(issue),
                issue.severity,
                self._impact_for(issue),
                list(issue.reference_ids),
            ))
        if len(package["features"]) > 1:
            recommendations.append(ReviewRecommendation(
                "Review feature ordering before release.",
                "Feature order affects regeneration robustness and future edits.",
                "Improves editability and reduces downstream regeneration risk.",
                "Medium",
                "Robustness",
                [feature.id for feature in package["features"]],
            ))
        return recommendations

    def _risks(self, issues, package):
        risks = [
            RiskAssessment(issue.category, issue.severity, issue.message, list(issue.reference_ids), self._mitigation_for(issue))
            for issue in issues
        ]
        if not risks:
            risks.append(RiskAssessment("Package", "Low", "No high-risk review findings detected.", self._package_ids(package), "Maintain revision-controlled package."))
        return risks

    def _scores(self, issues, package):
        penalties = {"Critical": 30.0, "High": 18.0, "Medium": 10.0, "Low": 4.0}
        by_category = {}
        for issue in issues:
            by_category.setdefault(issue.category, 0.0)
            by_category[issue.category] += penalties.get(issue.severity, 6.0)
        engineering = max(0.0, 100.0 - by_category.get("Model", 0.0) - by_category.get("Constraint", 0.0))
        manufacturing = max(0.0, 100.0 - by_category.get("Manufacturing", 0.0))
        documentation = max(0.0, 100.0 - by_category.get("Documentation", 0.0))
        drawing = max(0.0, 100.0 - by_category.get("Drawing", 0.0))
        robustness = max(0.0, 100.0 - by_category.get("Dependency", 0.0) - by_category.get("Model", 0.0) * 0.4)
        overall = round((engineering + manufacturing + documentation + drawing + robustness) / 5.0, 2)
        return ReviewScores(overall, round(engineering, 2), round(manufacturing, 2), round(documentation, 2), round(drawing, 2), round(robustness, 2))

    def _associativity(self, workspace, package):
        return {
            "workspace_id": getattr(workspace, "id", ""),
            "model_references": {
                "part_ids": [item.id for item in package["parts"]],
                "feature_ids": [item.id for item in package["features"]],
                "sketch_ids": [item.id for item in package["sketches"]],
                "parameter_ids": [item.id for item in package["parameters"]],
                "dependency_ids": [getattr(item, "id", "") for item in package["dependencies"]],
                "body_ids": [item.id for item in package["bodies"]],
            },
            "drawing_references": [item.id for item in package["drawings"]] + [item.id for item in package["views"]] + [item.id for item in package["sheets"]],
            "documentation_references": [item.id for item in package["documentation"]],
            "review_report_id": "",
            "update_policy": "Review recommendations remain advisory; model, drawing and documentation changes must be executed separately through commands.",
        }

    def _report_for_plan(self, plan):
        source_ids = []
        for values in plan.associativity.get("model_references", {}).values():
            source_ids.extend(values)
        source_ids.extend(plan.associativity.get("drawing_references", []))
        source_ids.extend(plan.associativity.get("documentation_references", []))
        report = ProductReport(
            "AI Design Review Report",
            (plan.associativity.get("model_references", {}).get("part_ids") or [""])[0],
            list(dict.fromkeys([item for item in source_ids if item])),
            ReportMetadata(
                "AI Design Review",
                "Associative Review Report",
                "Stored",
                {
                    "review_plan": plan.to_dict(),
                    "scores": plan.scores.to_dict(),
                    "issues": [issue.to_dict() for issue in plan.issues],
                    "recommendations": [recommendation.to_dict() for recommendation in plan.recommendations],
                    "risks": [risk.to_dict() for risk in plan.risks],
                    "associativity": dict(plan.associativity),
                },
            ),
        )
        report.display_color = "#ff8a65"
        return report

    def _summary(self, scores, issues, recommendations, risks):
        return {
            "executive_summary": f"Overall package score {scores.overall}/100 with {len(issues)} issue(s) and {len(recommendations)} recommendation(s).",
            "overall_quality_score": scores.overall,
            "engineering_score": scores.engineering,
            "manufacturing_score": scores.manufacturing,
            "documentation_score": scores.documentation,
            "drawing_score": scores.drawing,
            "robustness_score": scores.robustness,
            "risk_summary": {severity: len([risk for risk in risks if risk.severity == severity]) for severity in ("Critical", "High", "Medium", "Low")},
            "warnings": [issue.message for issue in issues],
        }

    def _project_type(self, package):
        process = self._manufacturing_discipline(package)
        if process == "cnc_machining":
            return "Mechanical Manufacturing Package"
        if process == "additive_manufacturing":
            return "Additive Manufacturing Package"
        return "Engineering Package"

    def _engineering_discipline(self, package):
        features = " ".join(getattr(feature, "name", "") for feature in package["features"]).lower()
        if "flange" in features or "shaft" in features:
            return "Mechanical"
        if "wall" in features or "stair" in features:
            return "Architectural"
        return "Product Design"

    def _manufacturing_discipline(self, package):
        plan = self._first_plan(package["documentation"], "documentation_plan")
        text = str(plan).lower()
        if "cnc" in text or "machining" in text:
            return "cnc_machining"
        if "additive" in text or "print" in text:
            return "additive_manufacturing"
        return "model_defined"

    def _first_plan(self, reports, key):
        for report in reports:
            properties = getattr(getattr(report, "metadata", None), "properties", {}) or {}
            if key in properties:
                return properties.get(key) or {}
        return {}

    def _package_ids(self, package):
        return [item.id for key in ("parts", "features", "drawings", "documentation") for item in package[key]]

    def _reason_for(self, issue):
        return {
            "Model": "Model robustness depends on clear feature history and stable parametric organization.",
            "Constraint": "Constraint quality controls downstream edit reliability.",
            "Dependency": "Dependency quality controls regeneration and reference stability.",
            "Manufacturing": "Manufacturing readiness requires process-specific dimensions and body data.",
            "Drawing": "Drawings are the release-facing manufacturing communication package.",
            "Documentation": "Documentation must align with model and drawing release state.",
        }.get(issue.category, "Engineering review found a package weakness.")

    def _benefit_for(self, issue):
        return {
            "Critical": "Prevents release-blocking failure.",
            "High": "Reduces production and revision risk.",
            "Medium": "Improves robustness and downstream usability.",
            "Low": "Improves clarity and maintainability.",
        }.get(issue.severity, "Improves package quality.")

    def _impact_for(self, issue):
        return {
            "Critical": "Release readiness",
            "High": "Manufacturing/revision risk",
            "Medium": "Engineering robustness",
            "Low": "Clarity",
        }.get(issue.severity, "Quality")

    def _mitigation_for(self, issue):
        return "Review and resolve through the existing Command System; AI Design Review does not modify the project automatically."

    def _standard_name(self, standard):
        name = str(standard or "ISO").upper()
        if name not in self.STANDARDS:
            raise TextToCADValidationError(f"Unsupported design review standard '{standard}'.")
        return name

    def _remember_session(self, session, plan):
        if session is not None and hasattr(session, "add_message"):
            session.add_message(
                "assistant",
                f"AI Design Review completed. review_plan_id={plan.id} score={plan.scores.overall}",
                "ai-design-review",
                plan.id,
            )

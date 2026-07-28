import time
from dataclasses import dataclass, field
from uuid import uuid4

from engine.ai.text_to_cad import TextToCADValidationError
from engine.bim import (
    DetailView,
    DrawingScale,
    DrawingSheet,
    ElevationView,
    FloorPlanView,
    SectionView,
    View3D,
    ViewMetadata,
    ViewPlacement,
    ViewportReference,
)
from engine.commands.ai_cad_command import AIParametricCADCommand
from engine.commands.bim_command import AddBIMSheetCommand, AddBIMViewCommand, CreateBIMProjectCommand
from engine.commands.product_command import AddProductReportCommand
from engine.product import ProductReport, ReportMetadata


@dataclass
class DrawingViewPlan:
    """Associative engineering drawing view plan."""

    view_type: str
    name: str
    scale: str
    purpose: str
    referenced_ids: list = field(default_factory=list)
    placement: dict = field(default_factory=dict)
    section: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe view plan metadata."""

        return {
            "id": self.id,
            "view_type": self.view_type,
            "name": self.name,
            "scale": self.scale,
            "purpose": self.purpose,
            "referenced_ids": list(self.referenced_ids),
            "placement": dict(self.placement),
            "section": dict(self.section),
        }


@dataclass
class DrawingDimensionPlan:
    """Associative model dimension plan."""

    dimension_type: str
    name: str
    value: object
    unit: str
    association_id: str
    role: str = "manufacturing"
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe dimension plan metadata."""

        return dict(self.__dict__)


@dataclass
class DrawingAnnotationPlan:
    """Associative annotation and callout plan."""

    annotation_type: str
    text: str
    association_id: str
    standard: str
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe annotation plan metadata."""

        return dict(self.__dict__)


@dataclass
class DrawingSheetPlan:
    """Associative drawing sheet plan using existing BIM drawing sheets."""

    number: str
    name: str
    size: str
    standard: str
    projection: str
    view_ids: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe sheet plan metadata."""

        return {
            "id": self.id,
            "number": self.number,
            "name": self.name,
            "size": self.size,
            "standard": self.standard,
            "projection": self.projection,
            "view_ids": list(self.view_ids),
        }


@dataclass
class DrawingValidation:
    """Drawing plan validation result."""

    valid: bool
    warnings: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def to_dict(self):
        """Return JSON-safe validation metadata."""

        return {
            "valid": self.valid,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


@dataclass
class AIDrawingPlan:
    """Production AI Drawing Studio plan for an existing parametric CAD model."""

    prompt: str
    model_id: str
    standard: str
    drawing_type: str
    sheets: list
    views: list
    dimensions: list
    annotations: list
    associativity: dict
    validation: DrawingValidation
    explanation: dict
    diagnostics: dict
    command_label: str = "AI Drawing Studio"
    object_type: str = "AI Drawing Studio"
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe drawing plan metadata."""

        return {
            "id": self.id,
            "prompt": self.prompt,
            "model_id": self.model_id,
            "standard": self.standard,
            "drawing_type": self.drawing_type,
            "sheets": [sheet.to_dict() for sheet in self.sheets],
            "views": [view.to_dict() for view in self.views],
            "dimensions": [dimension.to_dict() for dimension in self.dimensions],
            "annotations": [annotation.to_dict() for annotation in self.annotations],
            "associativity": dict(self.associativity),
            "validation": self.validation.to_dict(),
            "explanation": dict(self.explanation),
            "diagnostics": dict(self.diagnostics),
        }


@dataclass
class AIDrawingResult:
    """Result of creating an associative AI drawing package."""

    plan: AIDrawingPlan
    command: AIParametricCADCommand
    diagnostics: dict

    def to_dict(self):
        """Return JSON-safe drawing execution result."""

        return {
            "plan": self.plan.to_dict(),
            "command": self.command.name,
            "diagnostics": dict(self.diagnostics),
        }


class AIDrawingStudio:
    """Plans associative production engineering drawings through existing commands."""

    STANDARDS = {
        "ISO": {"sheet": "A2", "projection": "First Angle", "precision": 2, "scale": "1:2"},
        "ANSI": {"sheet": "B", "projection": "Third Angle", "precision": 3, "scale": "1:2"},
        "DIN": {"sheet": "A2", "projection": "First Angle", "precision": 2, "scale": "1:2"},
        "JIS": {"sheet": "A2", "projection": "Third Angle", "precision": 2, "scale": "1:2"},
        "BS": {"sheet": "A2", "projection": "First Angle", "precision": 2, "scale": "1:2"},
    }

    VIEW_CLASSES = {
        "Front": ElevationView,
        "Top": FloorPlanView,
        "Right": ElevationView,
        "Isometric": View3D,
        "Section": SectionView,
        "Detail": DetailView,
    }

    def __init__(self, generative_design):

        self.generative_design = generative_design
        self.statistics = {
            "requests": 0,
            "successful": 0,
            "failed": 0,
            "drawing_generation_time_ms": 0.0,
            "views_generated": 0,
            "dimensions_generated": 0,
            "annotations_generated": 0,
            "sections_generated": 0,
            "validation_statistics": 0,
            "associativity_statistics": 0,
        }
        self.last_plan = None

    def plan(self, prompt, workspace, session=None, standard="ISO"):
        """Plan an associative engineering drawing without mutating the workspace."""

        started = time.perf_counter()
        try:
            model = self._resolve_model(workspace)
            standard_name = self._standard_name(standard)
            references = self._model_references(workspace, model)
            views = self._plan_views(prompt, model, references, standard_name)
            dimensions = self._plan_dimensions(workspace, model, references)
            annotations = self._plan_annotations(prompt, model, references, standard_name)
            sheets = self._plan_sheets(model, views, standard_name)
            associativity = self._associativity(workspace, model, references, sheets, views, dimensions, annotations)
            validation = self._validate(sheets, views, dimensions, annotations, associativity)
            if not validation.valid:
                raise TextToCADValidationError("; ".join(validation.errors))
            diagnostics = {
                "planning_time_ms": (time.perf_counter() - started) * 1000.0,
                "views": len(views),
                "dimensions": len(dimensions),
                "annotations": len(annotations),
                "sections": len([view for view in views if view.view_type == "Section"]),
                "associative_references": sum(len(value) for value in associativity.get("model_references", {}).values()),
            }
            plan = AIDrawingPlan(
                prompt,
                getattr(model, "id", ""),
                standard_name,
                self._drawing_type(prompt, model),
                sheets,
                views,
                dimensions,
                annotations,
                associativity,
                validation,
                self._explain(prompt, standard_name, sheets, views, dimensions, annotations, model),
                diagnostics,
            )
            self.last_plan = plan
            self.statistics["drawing_generation_time_ms"] += diagnostics["planning_time_ms"]
            return plan
        except Exception:
            self.statistics["failed"] += 1
            raise

    def execute(self, prompt, workspace, session=None, standard="ISO"):
        """Create drawing records through the existing Command System."""

        self.statistics["requests"] += 1
        try:
            plan = self.plan(prompt, workspace, session, standard)
            commands = self._commands_for_plan(workspace, plan)
            command = AIParametricCADCommand(workspace, plan, commands)
            workspace.command_manager.execute(command)
            self.statistics["successful"] += 1
            self.statistics["views_generated"] += len(plan.views)
            self.statistics["dimensions_generated"] += len(plan.dimensions)
            self.statistics["annotations_generated"] += len(plan.annotations)
            self.statistics["sections_generated"] += len([view for view in plan.views if view.view_type == "Section"])
            self.statistics["validation_statistics"] += 1
            self.statistics["associativity_statistics"] += len(plan.associativity.get("drawing_references", []))
            self._remember_session(session, plan)
            return AIDrawingResult(plan, command, self.diagnostics())
        except Exception:
            self.statistics["failed"] += 1
            raise

    def diagnostics(self):
        """Return AI Drawing Studio diagnostics."""

        data = dict(self.statistics)
        data["last_plan_id"] = getattr(self.last_plan, "id", "")
        data["last_standard"] = getattr(self.last_plan, "standard", "")
        data["last_drawing_type"] = getattr(self.last_plan, "drawing_type", "")
        return data

    def _resolve_model(self, workspace):
        if workspace is None:
            raise TextToCADValidationError("Workspace is required for associative drawing generation.")
        product = getattr(workspace, "product_manager", None)
        if product is None:
            raise TextToCADValidationError("ProductManager is required for associative drawing generation.")
        candidates = list(getattr(product, "parts", []) or [])
        if not candidates:
            candidates = list(getattr(product, "bodies", []) or [])
        if not candidates:
            candidates = list(getattr(product, "features", []) or [])
        if not candidates:
            raise TextToCADValidationError("AI Drawing Studio requires an existing editable parametric CAD model.")
        return candidates[-1]

    def _model_references(self, workspace, model):
        product = workspace.product_manager
        model_id = getattr(model, "id", "")
        feature_ids = [item.id for item in getattr(product, "features", []) if getattr(item, "part_id", "") == model_id or getattr(item, "body_id", "") == model_id]
        body_ids = [item.id for item in getattr(product, "bodies", []) if model_id in getattr(item, "part_ids", []) or not getattr(item, "part_ids", [])]
        sketch_ids = [item.id for item in getattr(product, "sketches", []) if getattr(item, "part_id", "") == model_id or getattr(item, "owner_id", "") == model_id]
        parameter_ids = [item.id for item in getattr(product, "parameters", []) if getattr(item, "owner_id", "") in {model_id, *feature_ids}]
        dimension_ids = [item.id for item in getattr(product, "sketch_dimensions", []) if getattr(item, "sketch_id", "") in sketch_ids]
        return {
            "part_ids": [model_id] if getattr(model, "type_name", "") == "ProductPart" else [],
            "body_ids": body_ids,
            "feature_ids": feature_ids,
            "sketch_ids": sketch_ids,
            "parameter_ids": parameter_ids,
            "dimension_ids": dimension_ids,
        }

    def _plan_views(self, prompt, model, references, standard):
        text = str(prompt or "").lower()
        base_refs = self._all_reference_ids(references)
        views = [
            DrawingViewPlan("Front", "Front Manufacturing View", self.STANDARDS[standard]["scale"], "Primary shape and height definition", base_refs, {"x": 30, "y": 40, "width": 110, "height": 80}),
            DrawingViewPlan("Top", "Top Manufacturing View", self.STANDARDS[standard]["scale"], "Envelope, hole and pattern definition", base_refs, {"x": 150, "y": 40, "width": 110, "height": 80}),
            DrawingViewPlan("Right", "Right Manufacturing View", self.STANDARDS[standard]["scale"], "Depth and side feature definition", base_refs, {"x": 270, "y": 40, "width": 110, "height": 80}),
            DrawingViewPlan("Isometric", "Associative Isometric Reference", "1:4", "Non-dimensioned manufacturing reference", base_refs, {"x": 30, "y": 140, "width": 120, "height": 90}),
        ]
        if self._requires_section(text, model, references):
            views.append(DrawingViewPlan("Section", "Section A-A", self.STANDARDS[standard]["scale"], "Internal wall and feature verification", base_refs, {"x": 170, "y": 140, "width": 110, "height": 90}, {"cutting_plane": "A-A", "hatching": True}))
        if self._requires_detail(text, references):
            views.append(DrawingViewPlan("Detail", "Detail B", "2:1", "Hole/thread/small feature enlargement", base_refs, {"x": 295, "y": 145, "width": 80, "height": 70}))
        return views

    def _plan_dimensions(self, workspace, model, references):
        product = workspace.product_manager
        dimensions = []
        parameters = [item for item in getattr(product, "parameters", []) if item.id in references.get("parameter_ids", [])]
        for parameter in parameters:
            name = getattr(parameter, "name", "Parameter")
            dimensions.append(DrawingDimensionPlan("Parametric", name, getattr(parameter, "value", ""), getattr(parameter, "unit", ""), parameter.id, self._dimension_role(name)))
        if not dimensions:
            for sketch_dimension in [item for item in getattr(product, "sketch_dimensions", []) if item.id in references.get("dimension_ids", [])]:
                dimensions.append(DrawingDimensionPlan(getattr(sketch_dimension, "dimension_type", "Sketch"), getattr(sketch_dimension, "name", "Sketch Dimension"), getattr(sketch_dimension, "value", ""), getattr(sketch_dimension, "unit", ""), sketch_dimension.id, "driving"))
        if not dimensions:
            dimensions.append(DrawingDimensionPlan("Reference", "Model Reference", "Associative", "", getattr(model, "id", ""), "reference"))
        return dimensions

    def _plan_annotations(self, prompt, model, references, standard):
        model_id = getattr(model, "id", "")
        annotations = [
            DrawingAnnotationPlan("General Note", "All dimensions are associative to the parametric model unless noted.", model_id, standard),
            DrawingAnnotationPlan("Manufacturing Note", self._manufacturing_note(prompt), model_id, standard),
            DrawingAnnotationPlan("Datum", "Datum A assigned to primary mounting/reference face.", model_id, standard),
            DrawingAnnotationPlan("Center Marks", "Center marks and centerlines required for circular and patterned features.", model_id, standard),
        ]
        if references.get("feature_ids"):
            annotations.append(DrawingAnnotationPlan("Feature Callout", "Feature callouts reference the editable feature history.", references["feature_ids"][0], standard))
        return annotations

    def _plan_sheets(self, model, views, standard):
        sheet = DrawingSheetPlan(
            "AI-001",
            f"{getattr(model, 'name', 'Model')} Production Drawing",
            self.STANDARDS[standard]["sheet"],
            standard,
            self.STANDARDS[standard]["projection"],
            [view.id for view in views],
        )
        return [sheet]

    def _associativity(self, workspace, model, references, sheets, views, dimensions, annotations):
        return {
            "workspace_id": getattr(workspace, "id", ""),
            "model_id": getattr(model, "id", ""),
            "model_references": references,
            "sheet_plan_ids": [sheet.id for sheet in sheets],
            "view_plan_ids": [view.id for view in views],
            "dimension_plan_ids": [dimension.id for dimension in dimensions],
            "annotation_plan_ids": [annotation.id for annotation in annotations],
            "drawing_references": [],
            "update_policy": "Existing dependency/update systems refresh associated drawing records when model references change.",
        }

    def _validate(self, sheets, views, dimensions, annotations, associativity):
        errors = []
        warnings = []
        if not sheets:
            errors.append("Drawing plan requires at least one sheet.")
        if not views:
            errors.append("Drawing plan requires at least one view.")
        if len({view.view_type for view in views}) != len(views):
            warnings.append("Multiple views share a view type; names keep them distinct.")
        if not dimensions:
            errors.append("Drawing plan requires associative dimension metadata.")
        if not annotations:
            errors.append("Drawing plan requires annotation metadata.")
        if not associativity.get("model_id"):
            errors.append("Drawing plan requires a stable model reference.")
        return DrawingValidation(not errors, warnings, errors)

    def _commands_for_plan(self, workspace, plan):
        commands = []
        if getattr(workspace.bim_manager, "active_project", None) is None:
            commands.append(CreateBIMProjectCommand(workspace, "AI Drawing Studio Documentation"))
        view_objects = {}
        for index, view_plan in enumerate(plan.views):
            view = self._view_object(view_plan, index)
            view_objects[view_plan.id] = view
            commands.append(AddBIMViewCommand(workspace, view))
        for sheet_plan in plan.sheets:
            sheet = DrawingSheet(sheet_plan.name, sheet_plan.number, f"{sheet_plan.standard} Title Block")
            sheet.display_color = "#64b5f6"
            for view_id in sheet_plan.view_ids:
                view = view_objects.get(view_id)
                view_plan = next((item for item in plan.views if item.id == view_id), None)
                if view is not None and view_plan is not None:
                    placement = view_plan.placement
                    sheet.add_viewport(ViewportReference(
                        view.id,
                        ViewPlacement(
                            float(placement.get("x", 0.0)),
                            float(placement.get("y", 0.0)),
                            float(placement.get("width", 100.0)),
                            float(placement.get("height", 80.0)),
                        ),
                        DrawingScale(view_plan.scale, self._scale_ratio(view_plan.scale)),
                    ))
            sheet.ai_drawing_plan_id = plan.id
            commands.append(AddBIMSheetCommand(workspace, sheet))
            plan.associativity["drawing_references"].append(sheet.id)
        report = self._report_for_plan(plan)
        commands.append(AddProductReportCommand(workspace, report))
        plan.associativity["drawing_references"].append(report.id)
        return commands

    def _view_object(self, view_plan, index):
        view_class = self.VIEW_CLASSES.get(view_plan.view_type, View3D)
        metadata = ViewMetadata(
            view_plan.purpose,
            "Engineering",
            view_plan.scale,
            {
                "ai_drawing_plan_id": view_plan.id,
                "view_type": view_plan.view_type,
                "referenced_ids": list(view_plan.referenced_ids),
                "section": dict(view_plan.section),
            },
        )
        view = view_class(view_plan.name, "", "", metadata)
        view.scale = view_plan.scale
        view.viewed_entity_ids = list(view_plan.referenced_ids)
        view.location.x = float(index * 18.0)
        view.display_color = "#4fc3f7"
        return view

    def _report_for_plan(self, plan):
        metadata = ReportMetadata(
            "AI Drawing Studio",
            "Associative Drawing Metadata",
            "Stored",
            {
                "drawing_plan": plan.to_dict(),
                "standards": self.STANDARDS[plan.standard],
                "associativity": dict(plan.associativity),
                "validation": plan.validation.to_dict(),
            },
        )
        report = ProductReport(f"{plan.standard} Associative Drawing Package", plan.model_id, self._all_reference_ids(plan.associativity["model_references"]), metadata)
        report.display_color = "#42a5f5"
        return report

    def _explain(self, prompt, standard, sheets, views, dimensions, annotations, model):
        return {
            "drawing_purpose": self._drawing_type(prompt, model),
            "chosen_views": [view.to_dict() for view in views],
            "dimension_strategy": [dimension.to_dict() for dimension in dimensions],
            "annotation_strategy": [annotation.to_dict() for annotation in annotations],
            "section_strategy": [view.to_dict() for view in views if view.view_type == "Section"],
            "drawing_standard": standard,
            "manufacturing_intent": self._manufacturing_note(prompt),
            "missing_information": [],
            "warnings": [],
        }

    def _drawing_type(self, prompt, model):
        text = str(prompt or "").lower()
        if "assembly" in text:
            return "Assembly Drawing"
        if "manufacturing" in text or "production" in text:
            return "Manufacturing Drawing"
        return f"{getattr(model, 'type_name', 'Parametric Model')} Drawing"

    def _dimension_role(self, name):
        lower = str(name).lower()
        if "hole" in lower or "thread" in lower or "wall" in lower:
            return "manufacturing"
        if "length" in lower or "width" in lower or "height" in lower or "diameter" in lower:
            return "overall"
        return "functional"

    def _requires_section(self, text, model, references):
        model_name = f"{getattr(model, 'name', '')} {getattr(model, 'type_name', '')}".lower()
        return any(word in text or word in model_name for word in ("section", "enclosure", "pipe", "wall", "shell", "internal")) or bool(references.get("body_ids"))

    def _requires_detail(self, text, references):
        return any(word in text for word in ("detail", "hole", "thread", "small", "tolerance")) or bool(references.get("dimension_ids"))

    def _manufacturing_note(self, prompt):
        text = str(prompt or "").lower()
        if "machin" in text or "cnc" in text:
            return "Machining drawing includes functional dimensions, datums and surface-finish callout metadata."
        if "print" in text or "3d" in text:
            return "Additive manufacturing drawing includes wall, orientation and material note metadata."
        if "laser" in text or "sheet" in text:
            return "Sheet fabrication drawing includes flat-pattern, cut-edge and material note metadata."
        return "Production drawing includes associative dimensions, notes, datums and feature callouts."

    def _standard_name(self, standard):
        name = str(standard or "ISO").upper()
        if name not in self.STANDARDS:
            raise TextToCADValidationError(f"Unsupported drawing standard '{standard}'.")
        return name

    def _scale_ratio(self, scale):
        text = str(scale or "1:1")
        if ":" in text:
            numerator, denominator = text.split(":", 1)
            return float(denominator) / max(float(numerator), 0.0001)
        return 1.0

    def _all_reference_ids(self, references):
        ids = []
        for values in references.values():
            ids.extend(list(values or []))
        return list(dict.fromkeys(ids))

    def _remember_session(self, session, plan):
        if session is not None and hasattr(session, "add_message"):
            session.add_message(
                "assistant",
                f"AI Drawing Studio executed. drawing_plan_id={plan.id} sheets={len(plan.sheets)} views={len(plan.views)}",
                "ai-drawing-studio",
                plan.id,
            )

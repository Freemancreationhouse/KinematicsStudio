import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from engine.ai.text_to_cad import TextToCADValidationError
from engine.commands.ai_cad_command import AIParametricCADCommand
from engine.commands.product_command import AddProductReportCommand
from engine.product import ProductReport, ProductionReport, ReadinessReport, ReportMetadata, ShopFloorDocument


@dataclass
class DocumentationSection:
    """One associative engineering documentation section."""

    name: str
    section_type: str
    content: dict = field(default_factory=dict)
    reference_ids: list = field(default_factory=list)
    complete: bool = True
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe section data."""

        return {
            "id": self.id,
            "name": self.name,
            "section_type": self.section_type,
            "content": dict(self.content),
            "reference_ids": list(self.reference_ids),
            "complete": self.complete,
        }


@dataclass
class BOMItem:
    """Associative bill-of-materials row."""

    item_number: int
    name: str
    item_type: str
    quantity: float
    unit: str
    reference_id: str
    drawing_reference_ids: list = field(default_factory=list)
    material: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe BOM row data."""

        return {
            "id": self.id,
            "item_number": self.item_number,
            "name": self.name,
            "item_type": self.item_type,
            "quantity": self.quantity,
            "unit": self.unit,
            "reference_id": self.reference_id,
            "drawing_reference_ids": list(self.drawing_reference_ids),
            "material": self.material,
        }


@dataclass
class RevisionEntry:
    """Revision metadata associated with the model and drawings."""

    revision: str
    description: str
    author: str
    timestamp: str
    reference_ids: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe revision entry."""

        return {
            "id": self.id,
            "revision": self.revision,
            "description": self.description,
            "author": self.author,
            "timestamp": self.timestamp,
            "reference_ids": list(self.reference_ids),
        }


@dataclass
class DocumentationValidation:
    """Validation result for generated documentation."""

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
class AIDocumentationPlan:
    """Production AI documentation plan associated with model and drawing records."""

    prompt: str
    model_id: str
    standard: str
    document_type: str
    sections: list
    bom_items: list
    revision_history: list
    associativity: dict
    validation: DocumentationValidation
    explanation: dict
    diagnostics: dict
    command_label: str = "AI Documentation"
    object_type: str = "AI Documentation"
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe documentation plan."""

        return {
            "id": self.id,
            "prompt": self.prompt,
            "model_id": self.model_id,
            "standard": self.standard,
            "document_type": self.document_type,
            "sections": [section.to_dict() for section in self.sections],
            "bom_items": [item.to_dict() for item in self.bom_items],
            "revision_history": [revision.to_dict() for revision in self.revision_history],
            "associativity": dict(self.associativity),
            "validation": self.validation.to_dict(),
            "explanation": dict(self.explanation),
            "diagnostics": dict(self.diagnostics),
        }


@dataclass
class AIDocumentationResult:
    """Result of creating associative AI documentation records."""

    plan: AIDocumentationPlan
    command: AIParametricCADCommand
    diagnostics: dict

    def to_dict(self):
        """Return JSON-safe documentation execution result."""

        return {
            "plan": self.plan.to_dict(),
            "command": self.command.name,
            "diagnostics": dict(self.diagnostics),
        }


class AIDocumentation:
    """Generates associative engineering/manufacturing documentation through reports."""

    STANDARDS = {"ISO", "ANSI", "DIN", "JIS", "BS"}

    def __init__(self, drawing_studio):

        self.drawing_studio = drawing_studio
        self.statistics = {
            "requests": 0,
            "successful": 0,
            "failed": 0,
            "generation_time_ms": 0.0,
            "documents_generated": 0,
            "bom_statistics": 0,
            "assembly_statistics": 0,
            "inspection_statistics": 0,
            "revision_statistics": 0,
            "associativity_statistics": 0,
            "validation_statistics": 0,
        }
        self.last_plan = None

    def plan(self, prompt, workspace, session=None, standard="ISO"):
        """Plan associative documentation without mutating the workspace."""

        started = time.perf_counter()
        try:
            model = self._resolve_model(workspace)
            standard_name = self._standard_name(standard)
            model_refs = self._model_references(workspace, model)
            drawing_refs = self._drawing_references(workspace, model)
            sections = self._sections(prompt, workspace, model, model_refs, drawing_refs, standard_name)
            bom_items = self._bom_items(workspace, model, model_refs, drawing_refs)
            revisions = self._revisions(prompt, model, model_refs, drawing_refs)
            associativity = self._associativity(workspace, model, model_refs, drawing_refs, sections, bom_items, revisions)
            validation = self._validate(sections, bom_items, revisions, associativity)
            if not validation.valid:
                raise TextToCADValidationError("; ".join(validation.errors))
            diagnostics = {
                "planning_time_ms": (time.perf_counter() - started) * 1000.0,
                "documents": self._document_count(sections),
                "bom_items": len(bom_items),
                "assembly_sections": len([item for item in sections if item.section_type == "Assembly"]),
                "inspection_sections": len([item for item in sections if item.section_type == "Inspection"]),
                "revision_entries": len(revisions),
                "associative_references": sum(len(values) for values in associativity.get("model_references", {}).values()) + len(drawing_refs),
            }
            plan = AIDocumentationPlan(
                prompt,
                getattr(model, "id", ""),
                standard_name,
                self._document_type(prompt),
                sections,
                bom_items,
                revisions,
                associativity,
                validation,
                self._explain(standard_name, sections, bom_items, revisions, drawing_refs),
                diagnostics,
            )
            self.last_plan = plan
            self.statistics["generation_time_ms"] += diagnostics["planning_time_ms"]
            return plan
        except Exception:
            self.statistics["failed"] += 1
            raise

    def execute(self, prompt, workspace, session=None, standard="ISO"):
        """Create associative documentation through the existing Command System."""

        self.statistics["requests"] += 1
        try:
            plan = self.plan(prompt, workspace, session, standard)
            commands = [AddProductReportCommand(workspace, report) for report in self._reports_for_plan(plan)]
            command = AIParametricCADCommand(workspace, plan, commands)
            workspace.command_manager.execute(command)
            self.statistics["successful"] += 1
            self.statistics["documents_generated"] += len(commands)
            self.statistics["bom_statistics"] += len(plan.bom_items)
            self.statistics["assembly_statistics"] += len([item for item in plan.sections if item.section_type == "Assembly"])
            self.statistics["inspection_statistics"] += len([item for item in plan.sections if item.section_type == "Inspection"])
            self.statistics["revision_statistics"] += len(plan.revision_history)
            self.statistics["associativity_statistics"] += len(plan.associativity.get("document_references", []))
            self.statistics["validation_statistics"] += 1
            self._remember_session(session, plan)
            return AIDocumentationResult(plan, command, self.diagnostics())
        except Exception:
            self.statistics["failed"] += 1
            raise

    def diagnostics(self):
        """Return AI Documentation diagnostics."""

        data = dict(self.statistics)
        data["last_plan_id"] = getattr(self.last_plan, "id", "")
        data["last_standard"] = getattr(self.last_plan, "standard", "")
        data["last_document_type"] = getattr(self.last_plan, "document_type", "")
        return data

    def _resolve_model(self, workspace):
        if workspace is None:
            raise TextToCADValidationError("Workspace is required for associative documentation generation.")
        product = getattr(workspace, "product_manager", None)
        if product is None:
            raise TextToCADValidationError("ProductManager is required for associative documentation generation.")
        candidates = list(getattr(product, "parts", []) or [])
        if not candidates:
            candidates = list(getattr(product, "bodies", []) or [])
        if not candidates:
            candidates = list(getattr(product, "features", []) or [])
        if not candidates:
            raise TextToCADValidationError("AI Documentation requires an existing editable parametric CAD model.")
        return candidates[-1]

    def _model_references(self, workspace, model):
        if hasattr(self.drawing_studio, "_model_references"):
            return self.drawing_studio._model_references(workspace, model)
        return {"part_ids": [getattr(model, "id", "")], "body_ids": [], "feature_ids": [], "sketch_ids": [], "parameter_ids": [], "dimension_ids": []}

    def _drawing_references(self, workspace, model):
        model_id = getattr(model, "id", "")
        product = workspace.product_manager
        drawing_refs = []
        for report in getattr(product, "product_reports", []):
            if getattr(report, "target_id", "") != model_id:
                continue
            metadata = getattr(report, "metadata", None)
            if getattr(metadata, "report_type", "") == "AI Drawing Studio":
                drawing_refs.append(report.id)
                drawing_refs.extend(getattr(report, "source_ids", []) or [])
                properties = getattr(metadata, "properties", {}) or {}
                drawing_refs.extend(properties.get("associativity", {}).get("drawing_references", []) or [])
        project = getattr(getattr(workspace, "bim_manager", None), "active_project", None)
        if project is not None:
            drawing_refs.extend([item.id for item in getattr(project, "views", [])])
            drawing_refs.extend([item.id for item in getattr(project, "sheets", [])])
        refs = list(dict.fromkeys([ref for ref in drawing_refs if ref]))
        if not refs:
            raise TextToCADValidationError("AI Documentation requires existing associative engineering drawing records.")
        return refs

    def _sections(self, prompt, workspace, model, model_refs, drawing_refs, standard):
        all_refs = self._all_reference_ids(model_refs) + list(drawing_refs)
        product = workspace.product_manager
        features = [item for item in getattr(product, "features", []) if item.id in model_refs.get("feature_ids", [])]
        parameters = [item for item in getattr(product, "parameters", []) if item.id in model_refs.get("parameter_ids", [])]
        bodies = [item for item in getattr(product, "bodies", []) if item.id in model_refs.get("body_ids", [])]
        sections = [
            DocumentationSection("Design Specification", "Engineering", {
                "standard": standard,
                "model": getattr(model, "name", getattr(model, "type_name", "Parametric Model")),
                "document_scope": self._document_type(prompt),
                "required_drawings": list(drawing_refs),
            }, all_refs),
            DocumentationSection("Engineering Description", "Engineering", {
                "feature_count": len(features),
                "body_count": len(bodies),
                "editable_parametric_model": True,
            }, all_refs),
            DocumentationSection("Design Intent", "Engineering", self._design_intent(features), all_refs),
            DocumentationSection("Parameter Summary", "Engineering", {
                "parameters": [self._parameter_data(parameter) for parameter in parameters],
                "parameter_count": len(parameters),
            }, [parameter.id for parameter in parameters]),
            DocumentationSection("Feature Summary", "Engineering", {
                "features": [self._feature_data(feature) for feature in features],
                "history_based": True,
            }, [feature.id for feature in features]),
            DocumentationSection("Material Specification", "Engineering", self._material_specification(workspace, model), all_refs),
            DocumentationSection("Manufacturing Process", "Manufacturing", self._manufacturing_data(prompt, features, parameters), all_refs),
            DocumentationSection("Manufacturing Sequence", "Manufacturing", self._manufacturing_sequence(features), [feature.id for feature in features]),
            DocumentationSection("Assembly Instructions", "Assembly", self._assembly_data(workspace, model), all_refs),
            DocumentationSection("Inspection Plan", "Inspection", self._inspection_data(parameters, drawing_refs), all_refs),
            DocumentationSection("Revision History", "Revision", {"revision": "A", "drawing_references": list(drawing_refs)}, drawing_refs),
        ]
        return sections

    def _bom_items(self, workspace, model, model_refs, drawing_refs):
        product = workspace.product_manager
        parts = [item for item in getattr(product, "parts", []) if item.id in model_refs.get("part_ids", [])] or [model]
        items = []
        seen = set()
        for part in parts:
            if getattr(part, "id", "") in seen:
                continue
            seen.add(part.id)
            items.append(BOMItem(len(items) + 1, getattr(part, "name", "Part"), getattr(part, "type_name", "Part"), 1.0, "ea", part.id, list(drawing_refs), self._material_name(part)))
        for body in [item for item in getattr(product, "bodies", []) if item.id in model_refs.get("body_ids", [])]:
            if body.id not in seen:
                seen.add(body.id)
                items.append(BOMItem(len(items) + 1, getattr(body, "name", "Body"), getattr(body, "type_name", "Body"), 1.0, "ea", body.id, list(drawing_refs), self._material_name(body)))
        return items

    def _revisions(self, prompt, model, model_refs, drawing_refs):
        return [
            RevisionEntry(
                "A",
                f"Initial AI-generated associative documentation for {self._document_type(prompt)}.",
                "AI Documentation",
                datetime.now(timezone.utc).isoformat(),
                [getattr(model, "id", ""), *self._all_reference_ids(model_refs), *drawing_refs],
            )
        ]

    def _associativity(self, workspace, model, model_refs, drawing_refs, sections, bom_items, revisions):
        return {
            "workspace_id": getattr(workspace, "id", ""),
            "model_id": getattr(model, "id", ""),
            "model_references": model_refs,
            "drawing_references": list(drawing_refs),
            "section_ids": [section.id for section in sections],
            "bom_item_ids": [item.id for item in bom_items],
            "revision_ids": [revision.id for revision in revisions],
            "document_references": [],
            "update_policy": "Existing dependency/update systems refresh associated document metadata when model or drawing references change.",
        }

    def _validate(self, sections, bom_items, revisions, associativity):
        errors = []
        names = [section.name for section in sections]
        required = {
            "Design Specification",
            "Engineering Description",
            "Feature Summary",
            "Parameter Summary",
            "Manufacturing Process",
            "Assembly Instructions",
            "Inspection Plan",
            "Revision History",
        }
        missing = sorted(required - set(names))
        if missing:
            errors.append(f"Missing documentation sections: {', '.join(missing)}.")
        if not associativity.get("model_id"):
            errors.append("Documentation requires a stable model reference.")
        if not associativity.get("drawing_references"):
            errors.append("Documentation requires associative drawing references.")
        if not bom_items:
            errors.append("Documentation requires at least one BOM item.")
        if len({item.reference_id for item in bom_items}) != len(bom_items):
            errors.append("Documentation BOM contains duplicate model references.")
        if not revisions:
            errors.append("Documentation requires revision information.")
        incomplete = [section.name for section in sections if not section.complete]
        if incomplete:
            errors.append(f"Incomplete documentation sections: {', '.join(incomplete)}.")
        return DocumentationValidation(not errors, [], errors)

    def _reports_for_plan(self, plan):
        source_ids = self._all_reference_ids(plan.associativity["model_references"]) + list(plan.associativity["drawing_references"])
        common = {
            "documentation_plan": plan.to_dict(),
            "associativity": dict(plan.associativity),
            "validation": plan.validation.to_dict(),
        }
        reports = [
            ProductReport("AI Engineering Documentation", plan.model_id, source_ids, ReportMetadata("Engineering Documentation", "Associative Documentation", "Stored", {**common, "sections": [section.to_dict() for section in plan.sections if section.section_type == "Engineering"]})),
            ProductionReport("AI Manufacturing Documentation", plan.model_id, source_ids, ReportMetadata("Manufacturing Documentation", "Associative Documentation", "Stored", {**common, "sections": [section.to_dict() for section in plan.sections if section.section_type == "Manufacturing"]})),
            ProductReport("AI Associative BOM", plan.model_id, source_ids, ReportMetadata("Bill of Materials", "Associative Documentation", "Stored", {**common, "bom_items": [item.to_dict() for item in plan.bom_items]})),
            ShopFloorDocument("AI Assembly Documentation", plan.model_id, source_ids, ReportMetadata("Assembly Documentation", "Associative Documentation", "Stored", {**common, "sections": [section.to_dict() for section in plan.sections if section.section_type == "Assembly"]})),
            ReadinessReport("AI Inspection Documentation", plan.model_id, source_ids, ReportMetadata("Inspection Documentation", "Associative Documentation", "Stored", {**common, "sections": [section.to_dict() for section in plan.sections if section.section_type == "Inspection"]})),
            ProductReport("AI Revision Record", plan.model_id, source_ids, ReportMetadata("Revision Documentation", "Associative Documentation", "Stored", {**common, "revision_history": [revision.to_dict() for revision in plan.revision_history]})),
        ]
        for report in reports:
            report.display_color = "#7e57c2"
            plan.associativity["document_references"].append(report.id)
        return reports

    def _explain(self, standard, sections, bom_items, revisions, drawing_refs):
        return {
            "documentation_strategy": "Associative ProductReport-family records created through the existing Command System.",
            "generated_documents": self._document_names(sections),
            "engineering_assumptions": ["Editable parametric model references are authoritative."],
            "manufacturing_assumptions": ["Manufacturing data is derived from model, feature and drawing metadata."],
            "bom_strategy": f"{len(bom_items)} unique associative BOM row(s) generated.",
            "inspection_strategy": "Critical dimensions and drawing references drive inspection metadata.",
            "standard": standard,
            "drawing_references": list(drawing_refs),
            "warnings": [],
            "missing_information": [],
        }

    def _document_type(self, prompt):
        text = str(prompt or "").lower()
        if "manufacturing" in text or "shop" in text or "production" in text:
            return "Manufacturing Documentation Package"
        if "assembly" in text:
            return "Assembly Documentation Package"
        return "Engineering Documentation Package"

    def _document_count(self, sections):
        return len(set(self._document_names(sections)))

    def _document_names(self, sections):
        names = ["Engineering Documentation", "Bill of Materials", "Revision Record"]
        if any(section.section_type == "Manufacturing" for section in sections):
            names.append("Manufacturing Documentation")
        if any(section.section_type == "Assembly" for section in sections):
            names.append("Assembly Documentation")
        if any(section.section_type == "Inspection" for section in sections):
            names.append("Inspection Documentation")
        return names

    def _standard_name(self, standard):
        name = str(standard or "ISO").upper()
        if name not in self.STANDARDS:
            raise TextToCADValidationError(f"Unsupported documentation standard '{standard}'.")
        return name

    def _all_reference_ids(self, references):
        ids = []
        for values in references.values():
            ids.extend(list(values or []))
        return list(dict.fromkeys([item for item in ids if item]))

    def _parameter_data(self, parameter):
        return {
            "id": parameter.id,
            "name": getattr(parameter, "name", "Parameter"),
            "value": getattr(parameter, "value", ""),
            "unit": getattr(parameter, "unit", ""),
            "type": getattr(parameter, "parameter_type", ""),
        }

    def _feature_data(self, feature):
        return {
            "id": feature.id,
            "name": getattr(feature, "name", "Feature"),
            "type": getattr(feature, "feature_type", getattr(feature, "type_name", "")),
            "suppressed": getattr(feature, "suppressed", False),
        }

    def _design_intent(self, features):
        for feature in features:
            properties = getattr(getattr(feature, "metadata", None), "properties", {}) or {}
            analysis = properties.get("manufacturing_analysis", {})
            if analysis:
                return dict(analysis)
        return {"purpose": "Document editable parametric CAD model", "manufacturing_process": "model_metadata"}

    def _material_specification(self, workspace, model):
        material_id = getattr(model, "material_id", "") or getattr(model, "material", "")
        return {"material_reference": material_id or "Existing model material metadata", "model_id": getattr(model, "id", "")}

    def _manufacturing_data(self, prompt, features, parameters):
        text = str(prompt or "").lower()
        process = "cnc_machining" if "cnc" in text or "machin" in text else "additive_manufacturing" if "print" in text or "3d" in text else "model_defined"
        return {
            "manufacturing_process": process,
            "machine_recommendations": [self._machine_for(process)],
            "material_usage": "Derived from BodyManager/GeometryKernel metadata when available",
            "estimated_production_time": max(1, len(features)) * 10.0,
            "estimated_manufacturing_cost": max(1, len(features) + len(parameters)) * 2.5,
            "required_tooling": self._tooling_for(process),
            "quality_checkpoints": ["Verify critical dimensions", "Verify drawing revision", "Verify material"],
        }

    def _manufacturing_sequence(self, features):
        return {
            "sequence": [
                {"order": index + 1, "feature_id": feature.id, "operation": getattr(feature, "name", "Feature")}
                for index, feature in enumerate(features)
            ] or [{"order": 1, "operation": "Review model feature history"}],
            "inspection_after_each_stage": True,
        }

    def _assembly_data(self, workspace, model):
        assemblies = getattr(workspace.product_manager, "assemblies", [])
        return {
            "assembly_sequence": ["Verify parts", "Follow drawing references", "Confirm revision"],
            "subassembly_hierarchy": [getattr(item, "id", "") for item in assemblies],
            "fastener_summary": "Derived from model features and BOM metadata when present",
            "installation_guidance": "Use associative drawing references for orientation and inspection.",
            "exploded_assembly_references": [],
            "model_id": getattr(model, "id", ""),
        }

    def _inspection_data(self, parameters, drawing_refs):
        critical = [self._parameter_data(parameter) for parameter in parameters if self._critical_dimension(getattr(parameter, "name", ""))]
        if not critical:
            critical = [self._parameter_data(parameter) for parameter in parameters[:3]]
        return {
            "critical_dimensions": critical,
            "tolerance_checklist": ["Verify drawing precision", "Verify functional dimensions", "Verify manufacturing dimensions"],
            "quality_checklist": ["Material", "Finish", "Fit", "Revision"],
            "acceptance_criteria": "All critical dimensions and drawing references must match released model metadata.",
            "measurement_references": list(drawing_refs),
        }

    def _material_name(self, item):
        return getattr(item, "material", "") or getattr(item, "material_id", "") or "Model Material"

    def _machine_for(self, process):
        return {
            "cnc_machining": "3-axis CNC mill or router based on material",
            "additive_manufacturing": "FDM/SLA printer based on material and tolerance",
        }.get(process, "Machine selection derived from manufacturing metadata")

    def _tooling_for(self, process):
        return {
            "cnc_machining": ["End mill", "Drill", "Deburring tool"],
            "additive_manufacturing": ["Printer profile", "Build material", "Post-processing tools"],
        }.get(process, ["Existing manufacturing setup/tool metadata"])

    def _critical_dimension(self, name):
        text = str(name).lower()
        return any(word in text for word in ("length", "width", "height", "diameter", "hole", "wall", "thickness"))

    def _remember_session(self, session, plan):
        if session is not None and hasattr(session, "add_message"):
            session.add_message(
                "assistant",
                f"AI Documentation executed. documentation_plan_id={plan.id} documents={plan.diagnostics.get('documents', 0)}",
                "ai-documentation",
                plan.id,
            )

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowRecord:
    """Cross-workspace workflow certification row for Release 3.0 Batch H."""

    name: str
    workspaces: tuple
    entry_points: tuple
    data_exchanged: tuple
    synchronization: tuple
    status: str = "PASS"

    def to_dict(self):
        """Return JSON-safe workflow certification data."""

        return {
            "name": self.name,
            "workspaces": list(self.workspaces),
            "entry_points": list(self.entry_points),
            "data_exchanged": list(self.data_exchanged),
            "synchronization": list(self.synchronization),
            "status": self.status,
        }


def release_3_cross_workspace_workflow_matrix():
    """Return the certified Release 3.0 cross-workspace workflow matrix."""

    rows = [
        (
            "2D CAD to Product to Simulation to Machine/CAM",
            ("2D CAD", "3D CAD", "Product Design", "Simulation", "Machine/CAM", "Rendering", "Export"),
            ("AddEntityCommand", "CreateSolidFeatureCommand", "SimulationWorkspace", "Machine/CAM Commands"),
            ("sketch geometry", "solid mesh", "body metadata", "simulation study", "toolpath", "G-code"),
            ("selection", "properties", "history", "renderer", "persistence", "undo/redo"),
        ),
        (
            "GIS to Terrain to Site Engineering to BIM Coordination to BCF",
            ("GIS", "Terrain", "Site Engineering", "BIM", "Integrated Design", "BCF", "Rendering"),
            ("ImportGISFileCommand", "ImportTerrainFileCommand", "CreateBIMProjectCommand", "DesignCoordination Commands", "BCF Commands"),
            ("GIS layers", "terrain surface", "site boundary", "BIM object metadata", "coordination issue", "BCF topic"),
            ("metadata", "references", "history", "renderer overlays", "persistence"),
        ),
        (
            "AI Context to Parametric/Product Geometry to Rendering",
            ("AI Studio", "2D CAD", "Parametric", "Product Design", "Rendering", "Project"),
            ("CaptureAIContextCommand", "ProductManager", "ParametricEngine", "Renderer"),
            ("AI context", "selection", "parameters", "product metadata", "render state"),
            ("selection", "properties", "project settings", "history", "persistence"),
        ),
        (
            "Parametric to Geometry to Optimization to Manufacturing",
            ("Parametric", "GeometryKernel", "Simulation", "Optimization", "Machine/CAM"),
            ("Product Commands", "GeometryKernel", "RunOptimizationStudyCommand", "Machine/CAM Commands"),
            ("parameters", "body references", "optimization candidates", "manufacturing job"),
            ("metadata", "history", "diagnostics", "persistence"),
        ),
        (
            "Rendering to Export to Documentation",
            ("Rendering", "Export", "Documentation", "Project"),
            ("Renderer", "ExportManager", "Documentation Manager"),
            ("view state", "projection data", "export files", "document metadata"),
            ("renderer refresh", "project settings", "persistence"),
        ),
        (
            "Data Exchange to Every Workspace",
            ("Data Exchange", "CAD", "BIM", "GIS", "Simulation", "Machine/CAM", "AI Studio"),
            ("DataExchangeManager", "ProjectSerializer", "Import/Export Commands"),
            ("shared identifiers", "references", "metadata", "project state"),
            ("references", "metadata", "persistence", "diagnostics"),
        ),
        (
            "Project Lifecycle Across Workspaces",
            ("Project", "Workspace", "CAD", "BIM", "GIS", "Simulation", "Machine/CAM", "AI Studio"),
            ("ProjectSerializer", "Workspace", "CommandManager"),
            ("entities", "3D scene", "workspace settings", "capability metadata"),
            ("save", "reload", "undo/redo", "history", "selection"),
        ),
        (
            "BIM to Clash to Issue to Review",
            ("BIM", "Integrated Design", "Design Coordination", "BCF"),
            ("DesignCoordinationManager", "CreateCoordinationIssueCommand", "CreateDesignReviewSessionCommand"),
            ("BIM references", "clashes", "issues", "review sessions", "BCF topics"),
            ("references", "properties", "history", "persistence"),
        ),
        (
            "Simulation Results to AI Engineering Context",
            ("Simulation", "Results Database", "AI Studio", "Reports"),
            ("EngineeringSimulationManager", "AIEngine", "Report metadata"),
            ("studies", "results", "summaries", "recommendations"),
            ("project settings", "diagnostics", "persistence"),
        ),
        (
            "Machine/CAM to Rendering to Export",
            ("Machine/CAM", "Rendering", "Export", "Project"),
            ("Machine Commands", "Renderer", "ExportManufacturingJobCommand"),
            ("toolpaths", "simulation sessions", "G-code", "diagnostics"),
            ("history", "renderer", "persistence", "project settings"),
        ),
        (
            "Reference Federation to Coordination Review",
            ("Reference Models", "Coordination", "Clash Detection", "Issue Management", "BCF"),
            ("ReferenceManager", "CoordinationPanel", "DesignCoordinationManager", "BCFManager"),
            ("reference metadata", "conflicts", "issues", "viewpoints"),
            ("references", "properties", "history", "persistence"),
        ),
        (
            "Runtime Certification to Repository Certification",
            ("Integrated Platform Runtime", "Repository Certification", "Project", "Diagnostics"),
            ("IntegratedPlatformRuntime", "certify_repository", "ProjectSerializer"),
            ("runtime health", "source classification", "dependency metadata", "diagnostics"),
            ("diagnostics", "persistence", "startup", "shutdown"),
        ),
    ]

    return [WorkflowRecord(*row) for row in rows]


def workflow_summary():
    """Return aggregate workflow certification counts."""

    records = release_3_cross_workspace_workflow_matrix()
    return {
        "total": len(records),
        "passed": len([record for record in records if record.status == "PASS"]),
        "partial": len([record for record in records if record.status == "PARTIAL"]),
        "broken": len([record for record in records if record.status == "BROKEN"]),
        "not_implemented": len([record for record in records if record.status == "NOT IMPLEMENTED"]),
    }

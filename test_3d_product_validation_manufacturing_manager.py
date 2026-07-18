from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ProductPart
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(4.0, 4.0, 2.0), name="Validation Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Validation Product")
part = manager.add_part(ProductPart("Validation Part", "Validation Mesh"))
sheet_part = manager.sheet_metal_manager.convert_part(part, name="Validation Sheet Metal")

category = manager.validation_manager.create_category("Manufacturing Readiness", "Foundation checks")
rule = manager.validation_manager.create_rule("Required Material", category, "Missing Data", "Warning")
session = manager.validation_manager.create_session("Part Validation", [part, sheet_part])
results = manager.validation_manager.run_validation(session, [rule], [part, sheet_part])

analysis = manager.analysis_manager.create_analysis(
    part,
    "Part Physical Analysis",
    mass=12.5,
    volume=4.0,
    surface_area=18.0,
    material_usage={"Aluminium": 4.0},
)
wall_rule = manager.manufacturing_validation_manager.create_rule(
    "Minimum Wall",
    "Minimum Wall Thickness",
    threshold=1.5,
)
draft_rule = manager.manufacturing_validation_manager.create_rule(
    "Draft Placeholder",
    "Draft Angle",
    threshold=3.0,
)
manufacturing_report = manager.manufacturing_validation_manager.create_report(
    part,
    [wall_rule, draft_rule],
    results,
    "Manufacturing Readiness Report",
)
validation_report = manager.product_report_manager.create_validation_report(part, results, "Validation Summary")
analysis_report = manager.product_report_manager.create_analysis_report(part, [analysis], "Analysis Summary")

validation_stats = manager.validation_manager.statistics()
analysis_stats = manager.analysis_manager.statistics()
manufacturing_stats = manager.manufacturing_validation_manager.statistics()
report_stats = manager.product_report_manager.statistics()

assert validation_stats.sessions == 1
assert validation_stats.rules == 1
assert validation_stats.results == 2
assert validation_stats.passed == 2
assert session.metadata.status == "Completed"
assert len(session.history) == 1
assert len(manager.validation_results_for(session)) == 2
assert analysis_stats.results == 1
assert analysis.physical_properties.mass == 12.5
assert analysis.physical_properties.volume == 4.0
assert analysis.physical_properties.surface_area == 18.0
assert analysis.manufacturing_properties.material_usage["Aluminium"] == 4.0
assert manufacturing_stats.rules == 2
assert manufacturing_stats.reports == 1
assert manufacturing_report.target_id == part.id
assert len(manufacturing_report.rule_ids) == 2
assert report_stats.reports == 2
assert report_stats.validation_reports == 1
assert report_stats.analysis_reports == 1
assert validation_report.source_ids == [result.id for result in results]
assert analysis_report.source_ids == [analysis.id]
assert len(workspace.scene3d.entities()) == 1
assert len(manager.dependency_edges) >= 8

print("3d-product-validation-manufacturing-manager-ok")

import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ProductPart


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(5.0, 3.0, 2.0), name="Persisted Validation Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Persisted Validation Product")
part = manager.add_part(ProductPart("Persisted Validation Part", "Persisted Validation Mesh"))
category = manager.validation_manager.create_category("Readiness")
rule = manager.validation_manager.create_rule("Persisted Rule", category, "Required Property", "Warning")
session = manager.validation_manager.create_session("Persisted Session", [part])
results = manager.validation_manager.run_validation(session, [rule], [part])
analysis = manager.analysis_manager.create_analysis(part, "Persisted Analysis", mass=9.0, volume=3.0, surface_area=12.0)
mfg_rule = manager.manufacturing_validation_manager.create_rule("Persisted Wall Rule", threshold=2.0)
mfg_report = manager.manufacturing_validation_manager.create_report(part, [mfg_rule], results, "Persisted Manufacturing Report")
validation_report = manager.product_report_manager.create_validation_report(part, results, "Persisted Validation Report")
analysis_report = manager.product_report_manager.create_analysis_report(part, [analysis], "Persisted Analysis Report")
workspace.selection.select(mfg_report)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "product_validation_manufacturing.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    assert restored.validation_sessions[0].name == "Persisted Session"
    assert restored.validation_categories[0].name == "Readiness"
    assert restored.validation_rules[0].rule_type == "Required Property"
    assert restored.validation_results[0].target_id == restored.parts[0].id
    assert restored.product_validation_statistics.results == 1
    assert restored.analysis_results[0].physical_properties.mass == 9.0
    assert restored.analysis_results[0].physical_properties.surface_area == 12.0
    assert restored.analysis_statistics.results == 1
    assert restored.manufacturing_rules[0].threshold == 2.0
    assert restored.manufacturing_reports[0].name == "Persisted Manufacturing Report"
    assert restored.manufacturing_reports[0].selected is True
    assert restored.manufacturing_statistics.reports == 1
    assert restored.product_reports[0].name == "Persisted Validation Report"
    assert restored.product_reports[1].name == "Persisted Analysis Report"
    assert restored.product_report_statistics.reports == 2
    assert restored.product_report_statistics.validation_reports == 1
    assert restored.product_report_statistics.analysis_reports == 1

print("3d-product-validation-manufacturing-persistence-ok")

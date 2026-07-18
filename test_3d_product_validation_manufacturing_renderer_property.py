import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ProductPart
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
mesh = MeshEntity(MeshData.box(4.0, 4.0, 2.0), name="Rendered Validation Mesh")
workspace.add_3d_entity(mesh)
manager = workspace.product_manager
manager.create_document("Rendered Validation Product")
part = manager.add_part(ProductPart("Rendered Validation Part", "Rendered Validation Mesh"))
category = manager.validation_manager.create_category("Rendered Category")
rule = manager.validation_manager.create_rule("Rendered Validation Rule", category, "Missing Data", "Warning")
session = manager.validation_manager.create_session("Rendered Session", [part])
results = manager.validation_manager.run_validation(session, [rule], [part])
analysis = manager.analysis_manager.create_analysis(part, "Rendered Analysis", mass=7.5, volume=2.5, surface_area=10.5)
mfg_rule = manager.manufacturing_validation_manager.create_rule("Rendered Wall Rule", threshold=1.2)
mfg_report = manager.manufacturing_validation_manager.create_report(part, [mfg_rule], results, "Rendered Manufacturing Report")
validation_report = manager.product_report_manager.create_validation_report(part, results, "Rendered Validation Report")
workspace.selection.select(results[0])

renderer = Renderer3D()
renderer.camera = Camera3D()
renderer.camera.resize(640, 480)
image = QImage(640, 480, QImage.Format_ARGB32)
image.fill(0)
painter = QPainter(image)
renderer.render(painter, workspace, 640, 480)
painter.end()

panel = PropertyPanel()
panel.set_workspace(workspace)

panel.show_selection([session])
assert panel.type.text() == "ValidationSession"
assert "Targets: 1" in panel.radius.text()
assert "Results: 1" in panel.radius.text()

panel.show_selection([rule])
assert panel.type.text() == "ValidationRule"
assert "Rule: Missing Data" in panel.radius.text()

panel.show_selection([results[0]])
assert panel.type.text() == "ValidationResult"
assert "Status: Passed" in panel.radius.text()

panel.show_selection([analysis])
assert panel.type.text() == "AnalysisResult"
assert "Mass:" in panel.radius.text()
assert "Surface Area:" in panel.height.text()

panel.show_selection([mfg_report])
assert panel.type.text() == "ManufacturingReport"
assert "Rules: 1" in panel.radius.text()

panel.show_selection([validation_report])
assert panel.type.text() == "ValidationReport"
assert "Report: Validation" in panel.radius.text()

panel.show_selection([part])
assert "Analysis: 1" in panel.radius.text()
assert "Mfg: 1" in panel.radius.text()
assert "Reports: 1" in panel.radius.text()

print("3d-product-validation-manufacturing-renderer-property-ok")

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.geometry import Vector3
from engine.product import (
    EngineeringMaterial,
    FinishMetadata,
    ManufacturingMetadata,
    MassProperties,
    MechanicalMetadata,
    MechanicalProperties,
    ParameterSet,
    PartParameter,
    ProductPart,
    ToleranceMetadata,
)
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
workspace.product_manager.create_document("Rendered Batch B Product", "mm", 3)
part = workspace.product_manager.add_part(ProductPart("Rendered Batch B Part", "mesh-rendered-b", location=Vector3()))
parameter = workspace.product_manager.add_parameter_item(PartParameter("Width", 42.0, "mm", owner_id=part.id))
workspace.product_manager.add_parameter_item(ParameterSet("Render Set", part.id, [parameter.id]))
material = workspace.product_manager.add_engineering_material_item(
    EngineeringMaterial("Glass Filled Nylon", density=1350.0, color="#26c6da")
)
workspace.product_manager.engineering_material_manager.assign_material(part, material)
workspace.product_manager.add_mechanical_metadata(
    MechanicalMetadata(
        part.id,
        MechanicalProperties(material.id, 1350.0, 0.003),
        MassProperties(4.05, 0.003, 1350.0),
        ManufacturingMetadata("Injection Molding", "GFN-001", "A", "Supplier"),
        ToleranceMetadata("ISO 2768-f"),
        FinishMetadata("SPI-B1"),
    )
)
workspace.selection.select(part)

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
panel.show_selection([part])

assert panel.type.text() == "ProductPart"
assert "Parameters: 1" in panel.radius.text()
assert "Sets: 1" in panel.radius.text()
assert "Material: Glass Filled Nylon" in panel.length.text()
assert "Mass: 4.05" in panel.width.text()
assert "Volume:" in panel.height.text()
assert "Process: Injection Molding" in panel.line_type.text()
assert "Tolerance: ISO 2768-f" in panel.line_weight.text()
assert "Finish: SPI-B1" in panel.angle.text()

print("3d-product-parameters-materials-renderer-property-ok")

from engine.ai import AIEngine, ParametricDesignResult, TextToCADValidationError
from engine.workspace.workspace import Workspace


workspace = Workspace("AI Parametric Designer Workspace")
ai = AIEngine()
session = ai.create_session("Designer Session", workspace)

plan, analysis, strategy = ai.design_parametric_model(
    "Create a 3d printable waterproof enclosure 120 x 80 x 40 mm wall thickness 2 mm",
    workspace,
    session,
)

assert plan.object_type == "enclosure"
assert analysis.design_domain in ("general", "consumer_product")
assert analysis.manufacturing_process == "3d_printable"
assert analysis.expected_loads == "light_service_load"
assert "Minimum printable wall thickness" in analysis.rules
assert strategy.base_feature == "Base Extrude"
assert "Wall Thickness" in strategy.feature_order
assert "Named parameters bind dimensions" in strategy.dependency_strategy
assert any(item["role"] == "manufacturing" for item in strategy.dimension_strategy)
assert len(workspace.product_manager.parts) == 0

result = ai.execute_parametric_design(
    "Create a cnc machined flange diameter 100 mm height 12 mm hole diameter 40 mm",
    workspace,
    session,
)

assert isinstance(result, ParametricDesignResult)
assert result.analysis.design_domain == "mechanical"
assert result.analysis.manufacturing_process == "cnc_machined"
assert "Hole" in result.strategy.feature_order
assert "Corner Radius" in result.strategy.feature_order
assert len(workspace.product_manager.parts) == 1
assert len(workspace.product_manager.features) == 1
assert len(workspace.product_manager.feature_trees) == 1
assert len(workspace.product_manager.feature_nodes) == 1
assert len(workspace.product_manager.feature_dependencies) == 1
assert len(workspace.product_manager.parameters) >= 4
assert len(workspace.product_manager.parameter_sets) == 1
assert len(workspace.product_manager.parameter_groups) == 1
assert len(workspace.product_manager.expressions) >= 3
assert len(workspace.product_manager.expression_bindings) >= 3
assert len(workspace.product_manager.bodies) == 1
assert workspace.product_manager.features[0].metadata.properties["complete_parametric_designer"] is True
assert workspace.product_manager.features[0].definition.parameters["manufacturing_analysis"]["manufacturing_process"] == "cnc_machined"
assert "FeatureManager" in result.text_to_cad_result.explanation["modeling_strategy"]["regeneration_strategy"]
assert workspace.command_manager.undo_count == 1

workspace.command_manager.undo()
assert len(workspace.product_manager.parts) == 0
assert len(workspace.product_manager.features) == 0
assert len(workspace.product_manager.parameters) == 0
assert len(workspace.product_manager.feature_trees) == 0

workspace.command_manager.redo()
assert len(workspace.product_manager.parts) == 1
assert len(workspace.product_manager.features) == 1
assert len(workspace.product_manager.parameters) >= 4

try:
    ai.execute_parametric_design(
        "Create a 3d printable enclosure length 80 width 40 height 30 wall thickness 0.5 mm",
        workspace,
        session,
    )
    raise AssertionError("Manufacturing rule violation must be rejected safely")
except TextToCADValidationError:
    pass

diagnostics = ai.diagnostics()["parametric_designer"]
assert diagnostics["successful"] == 1
assert diagnostics["failed"] == 1
assert diagnostics["constraint_generation"] >= 1
assert diagnostics["dimension_generation"] >= 3
assert diagnostics["feature_planning"] >= 1
assert diagnostics["manufacturing_analysis"] >= 2
assert diagnostics["dependency_planning"] >= 1

print("ai-parametric-designer-ok")

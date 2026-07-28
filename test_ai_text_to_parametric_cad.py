from engine.ai import AIEngine, TextToCADValidationError
from engine.commands.ai_cad_command import AIParametricCADCommand
from engine.workspace.workspace import Workspace


workspace = Workspace("AI Text CAD Workspace")
ai = AIEngine()
session = ai.create_session("Text CAD Session", workspace)

plan = ai.plan_parametric_cad("Create a waterproof box 120 x 80 x 30 mm", workspace, session)
assert plan.object_type == "box"
assert plan.dimensions["length"] == 120.0
assert plan.dimensions["width"] == 80.0
assert plan.dimensions["height"] == 30.0
assert plan.intent.environment == "waterproof"
assert [step.action for step in plan.steps][:3] == ["Resolve Context", "Create Product Part", "Create Sketch"]
assert workspace.command_manager.undo_count == 0
assert len(workspace.product_manager.parts) == 0

result = ai.execute_parametric_cad("Create a 3d printable enclosure length 100 width 70 height 35 mm wall thickness 2 mm", workspace, session)
assert isinstance(result.command, AIParametricCADCommand)
assert result.plan.object_type == "enclosure"
assert workspace.command_manager.undo_count == 1
assert len(workspace.product_manager.parts) == 1
assert len(workspace.product_manager.sketches) == 1
assert len(workspace.product_manager.sketch_geometry) >= 1
assert len(workspace.product_manager.sketch_dimensions) >= 2
assert len(workspace.product_manager.sketch_constraints) >= 2
assert len(workspace.product_manager.sketch_profiles) == 1
assert len(workspace.product_manager.features) == 1
assert workspace.product_manager.features[0].metadata.author == "AI Text-to-CAD"
assert workspace.product_manager.features[0].definition.parameters["dimensions"]["height"] == 35.0
assert workspace.product_manager.features[0].result.status == "Geometry Generated"
assert len(workspace.product_manager.bodies) == 1
assert len(workspace.product_manager.geometry_results) == 1
assert "ExecuteFeatureGeometryCommand" in result.explanation["commands_generated"]
assert result.explanation["regeneration_result"].startswith("Executed through Command System")

workspace.command_manager.undo()
assert len(workspace.product_manager.parts) == 0
assert len(workspace.product_manager.features) == 0

workspace.command_manager.redo()
assert len(workspace.product_manager.parts) == 1
assert len(workspace.product_manager.features) == 1

second = ai.execute_parametric_cad("Make that length 150 width 90 height 45 mm", workspace, session)
assert second.plan.object_type == "enclosure"
assert second.plan.resolved_entities["conversation_object_type"] == "enclosure"
assert ai.diagnostics()["text_to_cad"]["conversation_resolutions"] >= 1

try:
    ai.plan_parametric_cad("Make something beautiful", workspace, session)
    raise AssertionError("Ambiguous text-to-CAD request must be rejected safely")
except TextToCADValidationError:
    pass

assert len(workspace.product_manager.parts) == 2
assert workspace.command_manager.undo_count == 2

print("ai-text-to-parametric-cad-ok")

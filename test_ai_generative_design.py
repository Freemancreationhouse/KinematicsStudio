from engine.ai import AIEngine, GenerativeDesignResult, GenerativeDesignStudy, TextToCADValidationError
from engine.workspace.workspace import Workspace


workspace = Workspace("AI Generative Design Workspace")
ai = AIEngine()
session = ai.create_session("Generative Session", workspace)

study = ai.generate_design_alternatives(
    "Create a 3d printable enclosure 120 x 80 x 40 mm wall thickness 2 mm with minimum weight and printability",
    workspace,
    session,
    count=3,
)

assert isinstance(study, GenerativeDesignStudy)
assert len(study.alternatives) == 3
assert study.comparison["recommended"] == study.alternatives[0].name
assert [alternative.rank for alternative in study.alternatives] == [1, 2, 3]
assert len({alternative.id for alternative in study.alternatives}) == 3
assert len({tuple(sorted(alternative.plan.dimensions.items())) for alternative in study.alternatives}) == 3
assert len({tuple(alternative.strategy.feature_order) for alternative in study.alternatives}) == 3
assert all(alternative.analysis.manufacturing_process == "3d_printable" for alternative in study.alternatives)
assert all(alternative.evaluation.weighted_score > 0 for alternative in study.alternatives)
assert all("ranking_decision" in alternative.explanation for alternative in study.alternatives)
assert len(workspace.product_manager.parts) == 0

result = ai.execute_generative_design(
    "Create a cnc machined flange diameter 100 mm height 12 mm hole diameter 40 mm with machinability and lowest cost",
    workspace,
    session,
    count=3,
)

assert isinstance(result, GenerativeDesignResult)
assert len(result.study.alternatives) == 3
assert len(workspace.product_manager.parts) == 3
assert len(workspace.product_manager.features) == 3
assert len(workspace.product_manager.feature_trees) == 3
assert len(workspace.product_manager.feature_dependencies) == 3
assert len(workspace.product_manager.bodies) == 3
assert len(workspace.product_manager.parameter_sets) == 3
assert len(workspace.product_manager.parameter_groups) == 3
assert len(workspace.product_manager.parameters) >= 12
assert len(workspace.product_manager.expressions) >= 9
assert len(workspace.product_manager.expression_bindings) >= 9
assert workspace.command_manager.undo_count == 1
assert any(feature.metadata.properties.get("generative_recommended") is True for feature in workspace.product_manager.features)
assert all(feature.metadata.properties.get("generative_alternative_id") for feature in workspace.product_manager.features)
assert result.study.comparison["alternatives"][0]["score"] >= result.study.comparison["alternatives"][-1]["score"]

workspace.command_manager.undo()
assert len(workspace.product_manager.parts) == 0
assert len(workspace.product_manager.features) == 0
assert len(workspace.product_manager.parameters) == 0

workspace.command_manager.redo()
assert len(workspace.product_manager.parts) == 3
assert len(workspace.product_manager.features) == 3

try:
    ai.execute_generative_design(
        "Create a 3d printable enclosure length 80 width 40 height 30 wall thickness 0.5 mm",
        workspace,
        session,
        count=2,
    )
    raise AssertionError("Generative design must reject invalid manufacturing concepts safely")
except TextToCADValidationError:
    pass

diagnostics = ai.diagnostics()["generative_design"]
assert diagnostics["successful"] == 1
assert diagnostics["failed"] == 1
assert diagnostics["alternatives_generated"] >= 6
assert diagnostics["evaluation_statistics"] >= 3
assert diagnostics["ranking_statistics"] >= 2
assert diagnostics["constraint_satisfaction"] >= 3
assert diagnostics["execution_statistics"] > 0

print("ai-generative-design-ok")

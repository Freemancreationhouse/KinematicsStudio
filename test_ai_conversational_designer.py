import tempfile
from pathlib import Path

from engine.ai import (
    ConversationalPlan,
    ConversationalResult,
    AIEngine,
)
from engine.storage import ProjectSerializer
from engine.workspace.workspace import Workspace


workspace = Workspace("Conversational AI Designer Workspace")
ai = AIEngine()
session = ai.create_session("Conversational Designer Session", workspace)

plan = ai.plan_conversational_design(
    "Create a CNC machined flange diameter 100 mm height 12 mm hole diameter 40 mm in ISO units",
    workspace,
    session,
    True,
    "ISO",
)
assert isinstance(plan, ConversationalPlan)
assert plan.intent.action == "create"
assert plan.validation["valid"]
assert len(workspace.product_manager.parts) == 0

result = ai.execute_conversational_design(
    "Create a CNC machined flange diameter 100 mm height 12 mm hole diameter 40 mm in ISO units",
    workspace,
    session,
    "ISO",
)
assert isinstance(result, ConversationalResult)
assert result.executed
assert workspace.product_manager.parts
assert workspace.product_manager.features
assert result.plan.command_plan.command_type == "create"

feature = workspace.product_manager.features[-1]
workspace.selection.select(feature)

clarification = ai.execute_conversational_design(
    "Increase the selected feature thickness",
    workspace,
    session,
    "ISO",
)
assert not clarification.executed
assert clarification.clarification is not None
assert "target dimension" in clarification.clarification.question.lower()
assert len(workspace.product_manager.features) >= 1

rename = ai.execute_conversational_design(
    'Rename the selected feature to "Mounting Extrude"',
    workspace,
    session,
    "ISO",
)
assert rename.executed
assert workspace.product_manager.features[-1].name == "Mounting Extrude"

workspace.command_manager.undo()
assert workspace.product_manager.features[-1].name != "Mounting Extrude"
workspace.command_manager.redo()
assert workspace.product_manager.features[-1].name == "Mounting Extrude"

suppress = ai.execute_conversational_design(
    "Suppress this feature",
    workspace,
    session,
    "ISO",
)
assert suppress.executed
assert workspace.product_manager.features[-1].suppressed

unsuppress = ai.execute_conversational_design(
    "Unsuppress it",
    workspace,
    session,
    "ISO",
)
assert unsuppress.executed
assert not workspace.product_manager.features[-1].suppressed

edit = ai.execute_conversational_design(
    "Change this feature thickness to 25 mm",
    workspace,
    session,
    "ISO",
)
assert edit.executed
assert workspace.product_manager.features[-1].definition.options.distance == 25.0

workspace.command_manager.undo()
assert workspace.product_manager.features[-1].definition.options.distance != 25.0
workspace.command_manager.redo()
assert workspace.product_manager.features[-1].definition.options.distance == 25.0

regenerate = ai.execute_conversational_design(
    "Rebuild this feature",
    workspace,
    session,
    "ISO",
)
assert regenerate.executed
assert regenerate.plan.command_plan.command_type == "regenerate"

memory = ai.conversational_designer._memory(workspace, session)
assert memory.recent_operations
assert memory.pending_clarifications
assert memory.user_preferences["preferred_units"] == "mm"
assert memory.user_preferences["preferred_standard"] == "ISO"

with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / "ai_conversational_designer.ksproj"
    ProjectSerializer().save(workspace, path)
    restored = ProjectSerializer().load(path)
    assert restored.product_manager.features
    assert restored.product_manager.features[-1].name == "Mounting Extrude"

diagnostics = ai.diagnostics()["conversational_designer"]
assert diagnostics["conversation_count"] >= 6
assert diagnostics["intent_resolution_statistics"] >= 6
assert diagnostics["clarification_statistics"] >= 1
assert diagnostics["command_statistics"] >= 5
assert diagnostics["execution_statistics"] >= 5
assert diagnostics["validation_statistics"] >= 6

print("ai-conversational-designer-ok")

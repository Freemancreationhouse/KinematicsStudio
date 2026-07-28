from pathlib import Path

from engine.ai import AIProvider, AIProviderCapabilities, PromptTemplate
from engine.cad import CADApplication
from engine.commands.command import Command
from engine.entities import MeshEntity
from engine.geometry import MeshData


class TestProvider(AIProvider):
    provider_id = "studio-test"
    display_name = "Studio Test Provider"

    @property
    def capabilities(self):
        return AIProviderCapabilities(chat=True, streaming=False, models=["studio-test-model"])

    def execute(self, task, progress):
        progress(0.4, "context received")
        return {
            "task_id": task.id,
            "context_workspace": task.context["workspace"]["name"],
            "selection_count": len(task.context["selection"]),
        }


class AddMetadataCommand(Command):
    def __init__(self, target):
        self.target = target
        self.previous = None

    def execute(self):
        self.previous = getattr(self.target, "name", "")
        self.target.name = "AI Command Applied"

    def undo(self):
        self.target.name = self.previous


app = CADApplication()
ai = app.engine.ai_engine
workspace = app.workspace
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="AI Context Mesh")
workspace.add_3d_entity(mesh)
workspace.selection.select(mesh)

context = ai.build_context(workspace)
assert context["workspace"]["name"] == workspace.name
assert context["selection"][0]["name"] == "AI Context Mesh"

ai.prompts.add(PromptTemplate("base", "Workspace: $workspace_name"))
ai.prompts.add(PromptTemplate("selection", "Selected: $selected_names", parent="base"))
rendered = ai.prompts.render("selection", ai.prompts.workspace_variables(workspace))
assert "Workspace: Model" in rendered
assert "Selected: AI Context Mesh" in rendered

session = ai.create_session("AI Studio Session", workspace)
provider = ai.register_provider(TestProvider())
ai.switch_provider(provider.provider_id)
assert any(item["provider_id"] == provider.provider_id for item in ai.providers_available())

task = ai.execute("Inspect current selection", workspace, session=session, background=True)
result = ai.runtime.result(task.id, timeout=5)
assert result["context_workspace"] == "Model"
assert result["selection_count"] == 1
assert ai.diagnostics()["completed"] == 1

cancelled = ai.runtime.submit("Cancel me", context, background=True)
assert ai.cancel(cancelled.id) is True

ai.execute_commands(workspace, [AddMetadataCommand(mesh)])
assert mesh.name == "AI Command Applied"
workspace.command_manager.undo()
assert mesh.name == "AI Context Mesh"

path = Path("ai_studio_foundation_validation.ksproj")
app.save_project(path)
assert app.workspace.project_settings["ai_studio"]["sessions"]["active_session_id"] == session.id
assert app.workspace.project_settings["ai_studio"]["prompts"]["templates"]

app.open_project(path)
assert app.engine.ai_engine.sessions.active_session_id == session.id
assert app.engine.ai_engine.prompts.render("base", {"workspace_name": "Loaded"}) == "Workspace: Loaded"

path.unlink(missing_ok=True)

print("ai-studio-foundation-ok")

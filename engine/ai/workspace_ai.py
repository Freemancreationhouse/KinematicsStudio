from engine.ai.context import AIContextEngine


class WorkspaceAI:
    """Compatibility wrapper for Workspace-derived AI context generation."""

    def __init__(self):
        self.context_engine = AIContextEngine()

    def analyze(self, workspace):
        """Return production Workspace context metadata."""

        return self.context_engine.build(workspace)

    def detect(self, workspace):
        """Return the workspace template/category from existing project settings."""

        settings = getattr(workspace, "project_settings", {}) or {}
        return settings.get("template", getattr(workspace, "name", ""))

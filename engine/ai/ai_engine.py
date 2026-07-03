from .assistant import AIAssistant
from .workspace_ai import WorkspaceAI


class AIEngine:

    def __init__(self):

        self.assistant = AIAssistant()
        self.workspace = WorkspaceAI()

    # ------------------------------------

    def execute(self, prompt):

        return self.assistant.execute(prompt)

    # ------------------------------------

    def analyze_workspace(self, workspace):

        return self.workspace.analyze(workspace)
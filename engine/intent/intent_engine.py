from engine.intent.design_intent import DesignIntent
from engine.intent.confidence import Confidence
from engine.intent.workspace import Workspace


class IntentEngine:

    def __init__(self):

        self.confidence = Confidence()

        self.workspace = Workspace.GENERAL

    # ---------------------------------

    def analyze(self, recognition):

        intent = DesignIntent()

        intent.shape = recognition["shape"]

        intent.workspace = self.workspace

        intent.confidence = self.confidence.calculate(

            recognition["shape"]

        )

        intent.metadata = recognition

        return intent
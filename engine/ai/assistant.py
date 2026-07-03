from engine.ai.prompt_parser import PromptParser
from engine.ai.model_generator import ModelGenerator


class AIAssistant:

    def __init__(self):

        self.parser = PromptParser()
        self.generator = ModelGenerator()

    # ----------------------------------------

    def execute(self, prompt):

        intent = self.parser.parse(prompt)

        result = self.generator.generate(intent)

        return result
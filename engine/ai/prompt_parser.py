from engine.ai.design_intent import DesignIntent


class PromptParser:

    def parse(self, prompt: str):

        text = prompt.lower()

        intent = DesignIntent()

        intent.prompt = prompt

        # -------- Workspace --------

        if "architecture" in text:
            intent.workspace = "architecture"

        elif "product" in text:
            intent.workspace = "product"

        elif "jewelry" in text:
            intent.workspace = "jewelry"

        elif "furniture" in text:
            intent.workspace = "furniture"

        # -------- Action --------

        if "create" in text:
            intent.action = "create"

        elif "generate" in text:
            intent.action = "generate"

        elif "design" in text:
            intent.action = "design"

        # -------- Object --------

        keywords = [

            "chair",
            "table",
            "lamp",
            "building",
            "wall",
            "door",
            "window",
            "ring",
            "facade"

        ]

        for word in keywords:

            if word in text:

                intent.object_type = word

                break

        intent.confidence = 0.80

        return intent
from engine.ai.design_intent import DesignIntent


class PromptParser:

    def parse(self, prompt: str):

        text = prompt.lower()

        intent = DesignIntent()

        intent.prompt = prompt
        matched = 0

        # -------- Workspace --------

        if "architecture" in text:
            intent.workspace = "architecture"
            matched += 1

        elif "product" in text:
            intent.workspace = "product"
            matched += 1

        elif "jewelry" in text:
            intent.workspace = "jewelry"
            matched += 1

        elif "furniture" in text:
            intent.workspace = "furniture"
            matched += 1

        # -------- Action --------

        if "create" in text:
            intent.action = "create"
            matched += 1

        elif "generate" in text:
            intent.action = "generate"
            matched += 1

        elif "design" in text:
            intent.action = "design"
            matched += 1

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
                matched += 1

                break

        intent.confidence = min(matched / 3.0, 1.0)

        return intent

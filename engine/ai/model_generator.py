class ModelGenerator:

    def generate(self, intent):

        return {

            "status": "ok",

            "workspace": intent.workspace,

            "action": intent.action,

            "object": intent.object_type,

            "style": intent.style,

            "message":
                f"Generating {intent.object_type}..."

        }
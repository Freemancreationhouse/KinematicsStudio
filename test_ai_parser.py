from engine.ai.prompt_parser import PromptParser

parser = PromptParser()

intent = parser.parse(

    "Create a modern wooden chair"

)

print(intent)
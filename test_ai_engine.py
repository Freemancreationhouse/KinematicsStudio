from engine.ai import AIEngine

ai = AIEngine()

result = ai.execute(

    "Create chair"

)

print(result["status"])
print(result["action"])
print(result["object"])
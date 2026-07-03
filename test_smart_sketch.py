from engine.smart_sketch import SmartSketchEngine

engine = SmartSketchEngine()

engine.begin()

engine.add(0, 0)
engine.add(20, 0)
engine.add(40, 0)
engine.add(60, 0)

result = engine.finish()

print(result["intent"])
print(result["entity"])
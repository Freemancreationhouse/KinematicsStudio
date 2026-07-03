from engine.core import modules

modules.register("cad", "CAD Engine")
modules.register("ai", "AI Engine")

print(modules.get("cad"))
print(modules.exists("ai"))
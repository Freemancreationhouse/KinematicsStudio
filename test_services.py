from engine.core import services

services.register("version", "2.0")

print(services.get("version"))

print(services.has("version"))
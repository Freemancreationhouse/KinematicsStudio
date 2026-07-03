from engine.workspace import WorkspaceManager

manager = WorkspaceManager()

manager.create("CAD")
manager.create("AI")
manager.create("CAM")

print(manager.names)

manager.set_active("AI")

print(manager.active.name)
from engine.cad import CADApplication

app = CADApplication()

print(app.workspace.name)

print(app.camera.zoom)

print(app.tool_manager.current)
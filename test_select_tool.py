from engine.tools import ToolManager, SelectTool

manager = ToolManager()

manager.register(SelectTool())

manager.mouse_press(None, (100, 200))
from PySide6.QtWidgets import QLineEdit


class CommandLine(QLineEdit):

    def __init__(self, tool_manager):
        super().__init__()

        self.tool_manager = tool_manager

        print("CommandLine Loaded")

        self.setPlaceholderText(
            "Command... (L, REC, C, M, TR, O, MI)"
        )

        self.returnPressed.connect(self.execute_command)

    def execute_command(self):

        print("ENTER PRESSED")

        cmd = self.text().strip().upper()

        print("Command =", cmd)

        commands = {
            "L": "polyline",
            "LINE": "polyline",

            "REC": "rectangle",
            "RECTANGLE": "rectangle",

            "C": "circle",
            "CIRCLE": "circle",

            "S": "select",
            "SELECT": "select",

            "M": "move",
            "MOVE": "move",

            "TR": "trim",
            "TRIM": "trim",

            "O": "offset",
            "OFFSET": "offset",

            "MI": "mirror",
            "MIRROR": "mirror",
        }

        if cmd in commands:

            print("Switching to", commands[cmd])

            self.tool_manager.set_tool(commands[cmd])

        else:

            print("Unknown Command")

        self.clear()
from PySide6.QtCore import Qt

from engine.geometry.trim import trim
from engine.commands.trim_command import TrimCommand


class TrimTool:

    def __init__(self):

        self.cutter = None

    # -------------------------------------------------

    def mouse_press(self, canvas, event):

        if event.button() != Qt.LeftButton:
            return

        clicked = None

        for entity in reversed(canvas.project.entities):

            if hasattr(entity, "hit_test"):

                if entity.hit_test(event.world_pos):

                    clicked = entity
                    break

        if clicked is None:
            return

        # -------- First Click --------

        if self.cutter is None:

            self.cutter = clicked

            print("Select object to trim")

            return

        # -------- Second Click --------

        target = clicked

        if target == self.cutter:

            self.cutter = None
            return

        new_line = trim(target, self.cutter)

        if new_line is None:

            self.cutter = None
            return

        cmd = TrimCommand(

            canvas.project,

            target,

            [new_line]

        )

        canvas.project.command_manager.do(cmd)

        self.cutter = None

        canvas.update()

    # -------------------------------------------------

    def mouse_move(self, canvas, event):
        pass

    # -------------------------------------------------

    def mouse_release(self, canvas, event):
        pass

    # -------------------------------------------------

    def draw_preview(self, painter):
        pass
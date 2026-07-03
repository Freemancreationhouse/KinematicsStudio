from PySide6.QtCore import Qt

from engine.geometry.mirror import mirror
from engine.commands.mirror_command import MirrorCommand


class MirrorTool:

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

        new_entity = mirror(clicked)

        if new_entity is None:
            return

        canvas.project.command_manager.do(

            MirrorCommand(

                canvas.project,

                new_entity

            )

        )

        canvas.update()

    def mouse_move(self, canvas, event):
        pass

    def mouse_release(self, canvas, event):
        pass

    def draw_preview(self, painter):
        pass
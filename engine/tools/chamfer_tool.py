from engine.commands import ChamferEntityCommand
from engine.geometry.chamfer import chamfer_entities, preview_chamfer
from engine.tools.corner_modify_tool import CornerModifyTool


class ChamferTool(CornerModifyTool):
    """Create line-line chamfers using the V2 command system."""

    operation_name = "Chamfer"
    value_name = "Distance"
    default_value = 5.0
    command_class = ChamferEntityCommand

    def _preview_entities(self):

        return preview_chamfer(
            self.first,
            self.second,
            self.value,
            self.first_pick,
            self.second_pick
        ) or []

    # --------------------------------

    def _replacement_entities(self):

        return chamfer_entities(
            self.first,
            self.second,
            self.value,
            self.first_pick,
            self.second_pick
        )

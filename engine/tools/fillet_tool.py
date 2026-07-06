from engine.commands import FilletEntityCommand
from engine.geometry.fillet import fillet_entities, preview_fillet
from engine.tools.corner_modify_tool import CornerModifyTool


class FilletTool(CornerModifyTool):
    """Create line-line fillets using the V2 command system."""

    operation_name = "Fillet"
    value_name = "Radius"
    default_value = 5.0
    command_class = FilletEntityCommand

    def _preview_entities(self):

        return preview_fillet(
            self.first,
            self.second,
            self.value,
            self.first_pick,
            self.second_pick
        ) or []

    # --------------------------------

    def _replacement_entities(self):

        return fillet_entities(
            self.first,
            self.second,
            self.value,
            self.first_pick,
            self.second_pick
        )

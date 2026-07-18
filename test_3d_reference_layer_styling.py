from engine.commands import (
    SaveReferenceDisplayPresetCommand,
    UpdateReferenceLayerMappingCommand,
    UpdateReferenceStyleCommand,
)
from engine.references3d import ReferenceModel
from engine.workspace.workspace import Workspace


workspace = Workspace()
model = workspace.reference_manager.add_model(ReferenceModel("Style Ref", "style.obj"))
instance = workspace.reference_manager.create_instance(model)
workspace.assign_layer(instance)

mapping = model.layer_mappings["Default"]
workspace.command_manager.execute(
    UpdateReferenceLayerMappingCommand(
        workspace,
        model,
        "Default",
        mapping.to_dict(),
        {
            **mapping.to_dict(),
            "visible": False,
            "locked": True,
            "isolated": True,
            "color_override": "#ff0000",
        },
    )
)

assert workspace.reference_manager.layer_statistics(model)["locked"] == 1
assert workspace.visible_references() == []
workspace.command_manager.undo()
assert workspace.visible_references() == [instance]

before = model.style_overrides.to_dict()
after = dict(before)
after.update({
    "display_color": "#00ff00",
    "transparency": 0.5,
    "wireframe_override": True,
    "display_mode_override": "X-Ray",
    "selection_highlight_override": "#ff00ff",
})
workspace.command_manager.execute(UpdateReferenceStyleCommand(workspace, model, before, after))
assert model.style_overrides.display_color == "#00ff00"
assert model.style_overrides.transparency == 0.5

workspace.command_manager.execute(SaveReferenceDisplayPresetCommand(workspace, model, "Review"))
assert "Review" in model.display_presets
workspace.command_manager.undo()
assert "Review" not in model.display_presets

print("3d-reference-layer-styling-ok")

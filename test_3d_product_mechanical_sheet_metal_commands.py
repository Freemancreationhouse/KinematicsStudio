from engine.commands import (
    AddMechanicalLibraryCommand,
    AddProductPartCommand,
    AddSheetMetalCommand,
    AddSheetMetalRuleCommand,
    CreateProductDocumentCommand,
)
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import (
    FlatPattern,
    MechanicalCategory,
    MechanicalComponent,
    MechanicalFamily,
    MechanicalLibrary,
    ProductPart,
    SheetMetalBody,
    SheetMetalPart,
    SheetMetalRule,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(2.0, 2.0, 0.5), name="Command Mechanical Sheet Mesh")
workspace.add_3d_entity(mesh)

workspace.command_manager.execute(CreateProductDocumentCommand(workspace, "Command Mechanical Sheet Product"))
part = ProductPart("Command Sheet Part", "Command Mechanical Sheet Mesh")
workspace.command_manager.execute(AddProductPartCommand(workspace, part))

library = MechanicalLibrary("Command Library")
workspace.command_manager.execute(AddMechanicalLibraryCommand(workspace, library))
category = MechanicalCategory("Bolts", library.id)
workspace.command_manager.execute(AddMechanicalLibraryCommand(workspace, category))
family = MechanicalFamily("Hex Bolts", library.id, category.id)
workspace.command_manager.execute(AddMechanicalLibraryCommand(workspace, family))
component = MechanicalComponent("M8 Hex Bolt", library.id, category.id, family.id, part.id)
workspace.command_manager.execute(AddMechanicalLibraryCommand(workspace, component))
rule = SheetMetalRule("Command Rule", thickness=1.5, inside_radius=0.75)
workspace.command_manager.execute(AddSheetMetalRuleCommand(workspace, rule))
sheet_part = SheetMetalPart("Command Sheet Metal", part.id)
sheet_part.rule_id = rule.id
workspace.command_manager.execute(AddSheetMetalCommand(workspace, sheet_part))
sheet_body = SheetMetalBody("Command Sheet Body", sheet_part.id, part.id, "Command Mechanical Sheet Mesh")
workspace.command_manager.execute(AddSheetMetalCommand(workspace, sheet_body))
flat_pattern = FlatPattern("Command Flat Pattern", sheet_part.id, sheet_body.id)
workspace.command_manager.execute(AddSheetMetalCommand(workspace, flat_pattern))

assert workspace.product_manager.mechanical_libraries == [library]
assert workspace.product_manager.mechanical_library_categories == [category]
assert workspace.product_manager.mechanical_families == [family]
assert workspace.product_manager.mechanical_library_components == [component]
assert workspace.product_manager.sheet_metal_rules == [rule]
assert workspace.product_manager.sheet_metal_parts == [sheet_part]
assert workspace.product_manager.sheet_metal_bodies == [sheet_body]
assert workspace.product_manager.flat_patterns == [flat_pattern]

workspace.command_manager.undo()
assert workspace.product_manager.flat_patterns == []
workspace.command_manager.undo()
assert workspace.product_manager.sheet_metal_bodies == []
workspace.command_manager.undo()
assert workspace.product_manager.sheet_metal_parts == []
workspace.command_manager.undo()
assert workspace.product_manager.sheet_metal_rules == []
workspace.command_manager.undo()
assert workspace.product_manager.mechanical_library_components == []

print("3d-product-mechanical-sheet-metal-commands-ok")

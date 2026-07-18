from engine.commands import (
    AddProductComponentCommand,
    AddProductPartCommand,
    CreateProductDocumentCommand,
)
from engine.product import Component, ComponentCategory, ComponentType, ProductPart
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.command_manager.execute(
    CreateProductDocumentCommand(workspace, "Command Product", "mm", 3)
)

part = ProductPart("Command Part", "mesh-001")
category = ComponentCategory("Purchased Parts")
component_type = ComponentType("Bearing", category.id)
component = Component("Bearing Component", part.id, component_type.id, category.id)

workspace.command_manager.execute(AddProductPartCommand(workspace, part))
workspace.command_manager.execute(AddProductComponentCommand(workspace, category))
workspace.command_manager.execute(AddProductComponentCommand(workspace, component_type))
workspace.command_manager.execute(AddProductComponentCommand(workspace, component))

assert workspace.product_manager.active_document.name == "Command Product"
assert workspace.product_manager.parts == [part]
assert workspace.product_manager.components_for(part) == [component]

workspace.command_manager.undo()
assert workspace.product_manager.components == []
assert part.component_ids == []
workspace.command_manager.redo()
assert workspace.product_manager.components == [component]
assert part.component_ids == [component.id]

workspace.command_manager.undo()
workspace.command_manager.undo()
assert workspace.product_manager.component_types == []
workspace.command_manager.redo()
assert workspace.product_manager.component_types == [component_type]

print("3d-product-foundation-commands-ok")

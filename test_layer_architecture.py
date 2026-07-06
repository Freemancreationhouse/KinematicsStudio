from engine.commands import AddEntityCommand
from engine.entities import CircleEntity, LineEntity, RectangleEntity
from engine.geometry import Vector2
from engine.layers.layer import Layer
from engine.layers.layer_manager import LayerManager
from engine.geometry.rotate import rotate_entities
from engine.workspace import Workspace


manager = LayerManager()
assert manager.count == 1
assert manager.current.name == "0"
assert manager.current.id == 0
assert manager.get("0") is manager.current
assert manager.get_by_id(0) is manager.current

construction = manager.create(
    "Construction",
    color="#FF0000",
    line_type="Dashed",
    line_weight=0.35,
)
duplicate = manager.create("Construction")
assert duplicate is construction
assert manager.count == 2
assert construction.id != manager.get("0").id
assert construction.color == "#FF0000"
assert construction.line_type == "Dashed"
assert construction.linetype == "Dashed"
assert construction.line_weight == 0.35

manager.set_current("Construction")
assert manager.current is construction
manager.set_current(construction.id)
assert manager.current is construction
manager.set_current(manager.get("0"))
assert manager.current.name == "0"

workspace = Workspace("Layer Test")
assert isinstance(workspace.current_layer, Layer)
assert workspace.current_layer.name == "0"
assert workspace.layer_manager.get("0") is workspace.current_layer

layer_a = workspace.layer_manager.create("A", "#00FF00")
workspace.set_current_layer("A")

line = LineEntity(Vector2(0, 0), Vector2(10, 0))
workspace.add_entity(line)
assert line.layer is layer_a
assert line.layer_id == layer_a.id
assert line.layer_name == "A"
assert line.color == "#00FF00"
assert line.display_color == "#00FF00"
assert line in layer_a.entities

layer_b = workspace.layer_manager.create("B", "#0000FF")
workspace.set_current_layer(layer_b)
rect = RectangleEntity(Vector2(0, 0), Vector2(10, 10))
workspace.command_manager.execute(AddEntityCommand(workspace.entities, rect))
assert rect.layer is layer_b
assert rect.layer_id == layer_b.id
assert rect.layer_name == "B"
assert rect.display_color == "#0000FF"
assert rect in layer_b.entities

workspace.update_layer_properties(layer_b, color="#112233")
assert rect.color == "#112233"
assert rect.display_color == "#112233"

replacement = rotate_entities(rect, Vector2(0, 0), 45)
workspace.assign_replacement_layer(rect, replacement)
assert all(entity.layer is layer_b for entity in replacement)
assert all(entity.display_color == "#112233" for entity in replacement)

workspace.command_manager.undo()
assert rect not in workspace.entities
assert rect not in layer_b.entities

workspace.command_manager.redo()
assert rect in workspace.entities
assert rect in layer_b.entities

layer_b.visible = False
assert rect not in workspace.visible_entities()
layer_b.visible = True
assert rect in workspace.visible_entities()

layer_b.locked = True
assert rect not in workspace.selectable_entities()
layer_b.locked = False
assert rect in workspace.selectable_entities()

workspace.set_current_layer("A")
circle = CircleEntity(Vector2(5, 5), 2)
workspace.entities.extend([circle])
assert circle.layer is layer_a

workspace.remove_entity(circle)
assert circle not in layer_a.entities

print("layer-architecture-ok")

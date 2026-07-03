from engine.workspace import LayerManager

manager = LayerManager()

manager.create("Default")
manager.create("Construction")
manager.create("Furniture")

print(manager.count)

print(manager.current.name)

manager.set_current(

    manager.layers[2]

)

print(manager.current.name)
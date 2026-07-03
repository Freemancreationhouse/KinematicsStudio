from engine.events import event_bus


def hello(name):

    print("Hello", name)


event_bus.subscribe("test", hello)

event_bus.emit("test", "Kinematics Studio")
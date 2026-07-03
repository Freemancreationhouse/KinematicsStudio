from engine.core import events


def hello(name):

    print("Hello", name)


events.subscribe("startup", hello)

events.emit("startup", "Kinematics Studio")
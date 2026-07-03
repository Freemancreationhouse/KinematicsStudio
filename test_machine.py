from engine.machine import MachineManager

m = MachineManager()

print(m.status)

m.connect("FluidNC")

print(m.status)

m.disconnect()

print(m.status)
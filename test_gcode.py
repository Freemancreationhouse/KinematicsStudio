from engine.machine import GCodeGenerator

g = GCodeGenerator()

g.generate_header()

g.add("G1 X100 Y50 F1500")

g.generate_footer()

print(g.export())
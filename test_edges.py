from engine.recognition.stroke import Stroke
from engine.recognition.edge_detector import EdgeDetector

stroke = Stroke()

stroke.add(0,0)
stroke.add(100,0)
stroke.add(100,60)
stroke.add(0,60)
stroke.add(0,0)

edges = EdgeDetector().detect(stroke.points)

print("Edges:", len(edges))

for e in edges:

    print(e)
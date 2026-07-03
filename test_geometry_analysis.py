from engine.recognition.stroke import Stroke

from engine.recognition.bounding_box import BoundingBox
from engine.recognition.aspect_ratio import AspectRatio
from engine.recognition.roundness import Roundness

stroke = Stroke()

stroke.add(0,0)
stroke.add(100,0)
stroke.add(100,60)
stroke.add(0,60)
stroke.add(0,0)

bbox = BoundingBox().calculate(stroke.points)

print(bbox)

print(

    "Aspect:",

    AspectRatio().calculate(bbox)

)

print(

    "Roundness:",

    Roundness().calculate(

        stroke.points,

        bbox

    )

)
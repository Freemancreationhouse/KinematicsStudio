from engine.recognition.stroke import Stroke
from engine.recognition.recognizer import Recognizer

stroke = Stroke()

stroke.add(0,0)
stroke.add(100,0)
stroke.add(100,60)
stroke.add(0,60)
stroke.add(0,0)

recognizer = Recognizer()

result = recognizer.recognize(stroke)

print(result["shape"])
print(result["corners"])
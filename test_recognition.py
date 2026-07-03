from engine.recognition.stroke import Stroke
from engine.recognition.recognizer import Recognizer

stroke = Stroke()

stroke.add(0, 0)
stroke.add(10, 0)
stroke.add(20, 0)
stroke.add(30, 0)
stroke.add(40, 0)

recognizer = Recognizer()

result = recognizer.recognize(stroke)

print(result)
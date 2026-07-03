from engine.recognition.stroke import Stroke
from engine.recognition.recognizer import Recognizer

from engine.intent.intent_engine import IntentEngine


stroke = Stroke()

stroke.add(0,0)
stroke.add(50,0)
stroke.add(100,0)

recognizer = Recognizer()

recognition = recognizer.recognize(stroke)

intent = IntentEngine().analyze(recognition)

print(intent)
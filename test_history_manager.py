from engine.workspace import HistoryManager

history = HistoryManager()

history.add("Draw Line")
history.add("Draw Rectangle")
history.add("Move Entity")

print(history.count)
print(history.last)

history.clear()

print(history.count)
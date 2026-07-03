from engine.render import Camera
from engine.geometry import Vector2

camera = Camera()

p = Vector2(100, 50)

screen = camera.world_to_screen(p)

print(screen)

camera.pan(50, 20)

print(camera.world_to_screen(p))

camera.zoom_in()

print(camera.world_to_screen(p))
from engine.render import Camera, ViewTransform
from engine.geometry import Vector2

camera = Camera()

view = ViewTransform(camera)

p = Vector2(100, 50)

print(view.world_to_screen(p))

camera.zoom_in()

print(view.world_to_screen(p))

print(view.screen_to_world(view.world_to_screen(p)))
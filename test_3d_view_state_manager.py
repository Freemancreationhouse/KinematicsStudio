from engine.render import Camera3D
from engine.view_states import DisplayModeManager, ViewStateManager, VisualStyle, VisualStyleManager


camera = Camera3D()
camera.state.yaw = 12.0
camera.state.pitch = 24.0
camera.state.distance = 1234.0

views = ViewStateManager()
view = views.save_view("Iso", camera, "shaded_with_edges", "Default")
assert view.name == "Iso"
assert views.current is view
assert view.display_mode == "shaded_with_edges"

camera.state.yaw = 90.0
views.restore_view("Iso", camera)
assert camera.state.yaw == 12.0

views.rename("Iso", "Production Iso")
assert views.names() == ["Production Iso"]
views.delete("Production Iso")
assert views.names() == []

display = DisplayModeManager()
display.set_mode("X-Ray")
assert display.current_mode == "x_ray"
display.set_mode("unknown")
assert display.current_mode == "wireframe"

styles = VisualStyleManager()
custom = styles.add(VisualStyle("Studio", background="#000000", grid_visible=False))
styles.set_current("Studio")
assert styles.current is custom
assert styles.current.grid_visible is False

data = styles.to_dict()
restored = VisualStyleManager()
restored.from_dict(data)
assert restored.current.name == "Studio"
assert restored.current.background == "#000000"

print("3d-view-state-manager-ok")

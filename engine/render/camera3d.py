import math

from engine.geometry import BoundingBox3D, Matrix4, Ray3, Vector3
from engine.geometry.helpers3d import WORLD_UP, clamp


class Camera3DState:
    """Serializable camera state for project persistence and recovery."""

    def __init__(
        self,
        target=None,
        distance=600.0,
        yaw=45.0,
        pitch=35.0,
        projection_mode="perspective",
        field_of_view=60.0,
        near_clip=0.1,
        far_clip=100000.0,
        orthographic_scale=800.0,
    ):

        self.target = target or Vector3()
        self.distance = float(distance)
        self.yaw = float(yaw)
        self.pitch = float(pitch)
        self.projection_mode = projection_mode
        self.field_of_view = float(field_of_view)
        self.near_clip = float(near_clip)
        self.far_clip = float(far_clip)
        self.orthographic_scale = float(orthographic_scale)

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe camera state."""

        return {
            "target": {
                "x": self.target.x,
                "y": self.target.y,
                "z": self.target.z,
            },
            "distance": self.distance,
            "yaw": self.yaw,
            "pitch": self.pitch,
            "projection_mode": self.projection_mode,
            "field_of_view": self.field_of_view,
            "near_clip": self.near_clip,
            "far_clip": self.far_clip,
            "orthographic_scale": self.orthographic_scale,
        }

    # --------------------------------

    @staticmethod
    def from_dict(data):
        """Create a camera state from persisted data."""

        data = data or {}
        target = data.get("target", {})

        return Camera3DState(
            target=Vector3(
                target.get("x", 0.0),
                target.get("y", 0.0),
                target.get("z", 0.0),
            ),
            distance=data.get("distance", 600.0),
            yaw=data.get("yaw", 45.0),
            pitch=data.get("pitch", 35.0),
            projection_mode=data.get("projection_mode", "perspective"),
            field_of_view=data.get("field_of_view", 60.0),
            near_clip=data.get("near_clip", 0.1),
            far_clip=data.get("far_clip", 100000.0),
            orthographic_scale=data.get("orthographic_scale", 800.0),
        )


class Camera3D:
    """Reusable 3D camera supporting perspective and orthographic projection."""

    def __init__(self):

        self.state = Camera3DState()
        self.viewport_width = 1
        self.viewport_height = 1

    # --------------------------------

    @property
    def aspect_ratio(self):
        """Return the current viewport aspect ratio."""

        return max(1.0, self.viewport_width) / max(1.0, self.viewport_height)

    # --------------------------------

    @property
    def position(self):
        """Return the camera position derived from orbit state."""

        yaw = math.radians(self.state.yaw)
        pitch = math.radians(self.state.pitch)
        radius = max(self.state.distance, 0.001)
        horizontal = math.cos(pitch) * radius

        return Vector3(
            self.state.target.x + math.cos(yaw) * horizontal,
            self.state.target.y + math.sin(yaw) * horizontal,
            self.state.target.z + math.sin(pitch) * radius,
        )

    # --------------------------------

    @property
    def forward(self):
        """Return normalized view direction."""

        return (self.state.target - self.position).normalized()

    # --------------------------------

    @property
    def right(self):
        """Return normalized camera right vector."""

        right = self.forward.cross(WORLD_UP).normalized()

        if right.length_squared() == 0.0:
            return Vector3(1.0, 0.0, 0.0)

        return right

    # --------------------------------

    @property
    def up(self):
        """Return normalized camera up vector."""

        return self.right.cross(self.forward).normalized()

    # --------------------------------

    def resize(self, width, height):
        """Update viewport dimensions."""

        self.viewport_width = max(1, int(width))
        self.viewport_height = max(1, int(height))

    # --------------------------------

    def view_matrix(self):
        """Return the camera view matrix."""

        return Matrix4.look_at(self.position, self.state.target, WORLD_UP)

    # --------------------------------

    def projection_matrix(self):
        """Return the active projection matrix."""

        if self.state.projection_mode == "orthographic":
            width = self.state.orthographic_scale * self.aspect_ratio
            return Matrix4.orthographic(
                width,
                self.state.orthographic_scale,
                self.state.near_clip,
                self.state.far_clip,
            )

        return Matrix4.perspective(
            self.state.field_of_view,
            self.aspect_ratio,
            self.state.near_clip,
            self.state.far_clip,
        )

    # --------------------------------

    def view_projection_matrix(self):
        """Return the combined view-projection matrix."""

        return self.projection_matrix() @ self.view_matrix()

    # --------------------------------

    def project(self, point):
        """Project a world point into viewport pixel coordinates."""

        clip = self.view_projection_matrix().transform_point(point)

        if clip.z < -1.0 or clip.z > 1.0:
            return None

        return (
            (clip.x + 1.0) * 0.5 * self.viewport_width,
            (1.0 - (clip.y + 1.0) * 0.5) * self.viewport_height,
        )

    # --------------------------------

    def screen_ray(self, x, y):
        """Return a world-space ray from viewport coordinates."""

        nx = (2.0 * float(x) / max(1.0, self.viewport_width)) - 1.0
        ny = 1.0 - (2.0 * float(y) / max(1.0, self.viewport_height))

        if self.state.projection_mode == "orthographic":
            height = self.state.orthographic_scale
            width = height * self.aspect_ratio
            origin = (
                self.position +
                self.right * (nx * width * 0.5) +
                self.up * (ny * height * 0.5)
            )
            return Ray3(origin, self.forward)

        tangent = math.tan(math.radians(self.state.field_of_view) * 0.5)
        direction = (
            self.forward +
            self.right * (nx * tangent * self.aspect_ratio) +
            self.up * (ny * tangent)
        ).normalized()

        return Ray3(self.position, direction)

    # --------------------------------

    def home_view(self):
        """Restore the default production 3D view."""

        self.state = Camera3DState()

    # --------------------------------

    def reset_view(self):
        """Reset camera target and orbit."""

        self.home_view()

    # --------------------------------

    def fit_bounds(self, bounds=None):
        """Fit the camera around a 3D bounding box."""

        if bounds is None or not bounds.valid:
            bounds = BoundingBox3D()
            bounds.add(Vector3(-250.0, -250.0, 0.0))
            bounds.add(Vector3(250.0, 250.0, 250.0))

        size = bounds.size
        radius = max(size.x, size.y, size.z, 1.0)
        self.state.target = bounds.center
        self.state.distance = radius * 2.5
        self.state.orthographic_scale = radius * 2.0

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe camera data."""

        return self.state.to_dict()

    # --------------------------------

    def from_dict(self, data):
        """Restore camera data from a dictionary."""

        self.state = Camera3DState.from_dict(data)


class CameraController3D:
    """Mouse and keyboard navigation controller for Camera3D."""

    def __init__(self, camera):

        self.camera = camera

    # --------------------------------

    def orbit(self, dx, dy):
        """Orbit around the camera target."""

        self.camera.state.yaw += dx * 0.35
        self.camera.state.pitch = clamp(
            self.camera.state.pitch + dy * 0.35,
            -89.0,
            89.0,
        )

    # --------------------------------

    def pan(self, dx, dy):
        """Pan the camera target in view space."""

        scale = self.camera.state.distance / max(
            self.camera.viewport_width,
            self.camera.viewport_height,
            1,
        )
        right = self.camera.right
        up = self.camera.up
        self.camera.state.target = (
            self.camera.state.target -
            right * (dx * scale) +
            up * (dy * scale)
        )

    # --------------------------------

    def zoom(self, wheel_delta):
        """Zoom the camera by wheel delta."""

        factor = 0.9 if wheel_delta > 0 else 1.1
        self.camera.state.distance = clamp(
            self.camera.state.distance * factor,
            1.0,
            1000000.0,
        )
        self.camera.state.orthographic_scale = clamp(
            self.camera.state.orthographic_scale * factor,
            1.0,
            1000000.0,
        )

    # --------------------------------

    def fit_view(self, bounds=None):
        """Fit the camera to available 3D bounds."""

        self.camera.fit_bounds(bounds)

    # --------------------------------

    def home_view(self):
        """Restore the default camera home view."""

        self.camera.home_view()

    # --------------------------------

    def reset_view(self):
        """Reset the camera view."""

        self.camera.reset_view()

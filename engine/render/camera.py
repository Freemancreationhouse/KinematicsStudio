from engine.geometry import Vector2


class Camera:

    def __init__(self):

        self.position = Vector2(0, 0)

        self.zoom = 1.0
        self.min_zoom = 0.01
        self.max_zoom = 100.0

    # --------------------------------

    def pan(self, dx, dy):

        self.position.x += dx
        self.position.y += dy

    # --------------------------------

    def zoom_in(self, factor=1.1):

        if factor > 0:
            self.zoom = min(self.zoom * factor, self.max_zoom)

    # --------------------------------

    def zoom_out(self, factor=1.1):

        if factor > 0:
            self.zoom = max(self.zoom / factor, self.min_zoom)

    # --------------------------------

    def zoom_at(self, screen_point, factor):

        if factor <= 0:
            return

        before = self.screen_to_world(screen_point)

        self.zoom = max(
            self.min_zoom,
            min(self.zoom * factor, self.max_zoom)
        )

        after = self.screen_to_world(screen_point)

        self.position.x += before.x - after.x
        self.position.y += before.y - after.y

    # --------------------------------

    def fit_to_bounds(self, bounds, width, height, padding=40):

        if bounds is None:
            self.position = Vector2(0, 0)
            self.zoom = 1.0
            return

        view_width = max(1.0, width - padding * 2)
        view_height = max(1.0, height - padding * 2)
        bounds_width = max(1.0, bounds.width)
        bounds_height = max(1.0, bounds.height)

        self.zoom = max(
            self.min_zoom,
            min(
                min(view_width / bounds_width, view_height / bounds_height),
                self.max_zoom
            )
        )

        center = bounds.center
        self.position = Vector2(
            center.x - width / (2 * self.zoom),
            center.y - height / (2 * self.zoom)
        )

    # --------------------------------

    def world_to_screen(self, point):

        return Vector2(

            (point.x - self.position.x) * self.zoom,

            (point.y - self.position.y) * self.zoom

        )

    # --------------------------------

    def screen_to_world(self, point):

        return Vector2(

            point.x / self.zoom + self.position.x,

            point.y / self.zoom + self.position.y

        )

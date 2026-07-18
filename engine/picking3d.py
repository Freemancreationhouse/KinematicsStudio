import math
from dataclasses import dataclass


@dataclass
class PickHit:
    """3D picking hit result."""

    entity: object
    distance: float
    point: object


class PickingManager3D:
    """Ray-based 3D picking manager using workspace-owned scene entities."""

    def pick(self, workspace, ray, max_distance=1000000.0):
        """Return the nearest hit for a ray."""

        hits = self.pick_all(workspace, ray, max_distance)

        return hits[0] if hits else None

    # --------------------------------

    def pick_all(self, workspace, ray, max_distance=1000000.0):
        """Return all hits sorted by distance."""

        scene = getattr(workspace, "scene3d", None)

        if scene is None:
            return []

        candidates = (
            workspace.selectable_3d_entities()
            if hasattr(workspace, "selectable_3d_entities")
            else scene.visible_entities()
        )
        hits = []

        for entity in candidates:
            hit = self._pick_entity(entity, ray, max_distance)

            if hit is not None:
                hits.append(hit)

        return sorted(hits, key=lambda item: item.distance)

    # --------------------------------

    def hover(self, workspace, ray):
        """Set hover state on the nearest entity and return it."""

        scene = getattr(workspace, "scene3d", None)

        if scene is None:
            return None

        for entity in scene.entities():
            entity.hovered = False

        hit = self.pick(workspace, ray)

        if hit is not None:
            hit.entity.hovered = True
            return hit.entity

        return None

    # --------------------------------

    def _pick_entity(self, entity, ray, max_distance):

        sphere_distance = self._intersect_sphere(ray, entity.bounding_sphere)

        if sphere_distance is None or sphere_distance > max_distance:
            return None

        box_distance = self._intersect_box(ray, entity.bounding_box3d)

        if box_distance is None:
            return None

        return PickHit(entity, box_distance, ray.point_at(box_distance))

    # --------------------------------

    def _intersect_sphere(self, ray, sphere):

        oc = ray.origin - sphere.center
        a = ray.direction.dot(ray.direction)
        b = 2.0 * oc.dot(ray.direction)
        c = oc.dot(oc) - sphere.radius * sphere.radius
        discriminant = b * b - 4.0 * a * c

        if discriminant < 0.0:
            return None

        root = math.sqrt(discriminant)
        near = (-b - root) / (2.0 * a)
        far = (-b + root) / (2.0 * a)

        if near >= 0.0:
            return near

        if far >= 0.0:
            return far

        return None

    # --------------------------------

    def _intersect_box(self, ray, box):

        if not box.valid:
            return None

        t_min = 0.0
        t_max = float("inf")

        padding = 4.0

        for origin, direction, low, high in (
            (ray.origin.x, ray.direction.x, box.min.x, box.max.x),
            (ray.origin.y, ray.direction.y, box.min.y, box.max.y),
            (ray.origin.z, ray.direction.z, box.min.z, box.max.z),
        ):
            low -= padding
            high += padding

            if abs(direction) < 1e-9:
                if origin < low or origin > high:
                    return None
                continue

            inv = 1.0 / direction
            t1 = (low - origin) * inv
            t2 = (high - origin) * inv
            t1, t2 = min(t1, t2), max(t1, t2)
            t_min = max(t_min, t1)
            t_max = min(t_max, t2)

            if t_min > t_max:
                return None

        return t_min

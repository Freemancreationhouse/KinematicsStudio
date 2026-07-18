from engine.geometry.primitives import point_to_segment_distance, rectangle_edges


def hit_entity(workspace, point, tolerance=8.0):
    """Return the nearest selectable entity within a pick tolerance."""

    candidates = (
        workspace.selectable_entities()
        if hasattr(workspace, "selectable_entities")
        else workspace.entities
    )
    best = None
    best_distance = tolerance

    for entity in reversed(candidates):
        distance = entity_distance(entity, point)

        if distance is not None and distance < best_distance:
            best = entity
            best_distance = distance

    return best


def entity_distance(entity, point):
    """Return distance from a point to a supported entity."""

    if hasattr(entity, "start") and hasattr(entity, "end"):
        return point_to_segment_distance(point, entity.start, entity.end)

    if hasattr(entity, "p1") and hasattr(entity, "p2"):
        return min(
            point_to_segment_distance(point, start, end)
            for start, end in rectangle_edges(entity)
        )

    if hasattr(entity, "center") and hasattr(entity, "radius"):
        return abs(entity.center.distance_to(point) - entity.radius)

    if entity.hit_test(point):
        return 0.0

    return None

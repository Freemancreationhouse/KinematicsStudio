from engine.geometry.copy import copy_entities


def rectangular_array_entities(
    entity,
    rows,
    columns,
    row_spacing,
    column_spacing
):
    """Return rectangular array copies, excluding the source position."""

    generated = []

    for row in range(max(1, int(rows))):
        for column in range(max(1, int(columns))):
            if row == 0 and column == 0:
                continue

            generated.extend(
                copy_entities(
                    entity,
                    column * column_spacing,
                    row * row_spacing
                )
            )

    return generated


def preview_rectangular_array(
    entity,
    rows,
    columns,
    row_spacing,
    column_spacing
):
    """Return preview entities for a rectangular array operation."""

    return rectangular_array_entities(
        entity,
        rows,
        columns,
        row_spacing,
        column_spacing
    )


def array(entity, rows, columns, row_spacing, column_spacing):
    """Backward-compatible rectangular array helper."""

    return rectangular_array_entities(
        entity,
        rows,
        columns,
        row_spacing,
        column_spacing
    )

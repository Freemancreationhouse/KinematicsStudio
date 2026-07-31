from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any


class SelectionService:
    """Authoritative UI-free service for application selection operations."""

    def __init__(self, workspace: Any) -> None:
        """Create a selection service for an existing workspace."""

        self._workspace = workspace

    def workspace(self) -> Any:
        """Return the current workspace from a workspace or provider."""

        provider = self._workspace
        current_workspace = getattr(provider, "current_workspace", None)
        if callable(current_workspace):
            return current_workspace()

        current = getattr(provider, "current", None)
        if current is not None:
            return current

        workspace = getattr(provider, "workspace", None)
        if workspace is not None and workspace is not provider:
            return workspace

        return provider

    def selection(self) -> Any:
        """Return the underlying workspace selection manager."""

        return getattr(self.workspace(), "selection", None)

    def selected(self) -> list[Any]:
        """Return the current selected entities as a list."""

        selection = self.selection()
        if selection is None:
            return []
        value = getattr(selection, "selected", None)
        if callable(value):
            value = value()
        return list(value or [])

    def first(self) -> Any:
        """Return the first selected entity."""

        selection = self.selection()
        value = self._read_attr_or_call(selection, ("first",))
        if value is not None:
            return value
        items = self.selected()
        return items[0] if items else None

    def last(self) -> Any:
        """Return the last selected entity."""

        selection = self.selection()
        value = self._read_attr_or_call(selection, ("last",))
        if value is not None:
            return value
        items = self.selected()
        return items[-1] if items else None

    def count(self) -> int:
        """Return the current selection count."""

        selection = self.selection()
        value = self._read_attr_or_call(selection, ("count",))
        if value is not None:
            return int(value)
        return len(self.selected())

    def is_empty(self) -> bool:
        """Return True when no entities are selected."""

        return self.count() == 0

    def contains(self, entity: Any) -> bool:
        """Return True when an entity is currently selected."""

        return entity in self.selected()

    def select(self, entity: Any, additive: bool = False) -> Any:
        """Select a single entity through the existing selection manager."""

        selection = self.selection()
        if selection is None:
            return None
        return self._call_first(selection, ("select",), entity, additive)

    def select_many(self, items: Iterable[Any], additive: bool = False) -> Any:
        """Select many entities through the existing selection manager."""

        entities = list(items)
        selection = self.selection()
        if selection is None:
            return None
        select_many = getattr(selection, "select_many", None)
        if callable(select_many):
            try:
                select_many(entities, additive)
            except TypeError:
                select_many(entities)
            return self.selected()
        if not additive:
            self.clear()
        for entity in entities:
            self._call_first(selection, ("select",), entity, True)
        return self.selected()

    def deselect(self, entity: Any) -> Any:
        """Deselect a single entity through the existing selection manager."""

        selection = self.selection()
        if selection is None:
            return None
        return self._call_first(selection, ("deselect",), entity)

    def deselect_many(self, items: Iterable[Any]) -> list[Any]:
        """Deselect many entities through the existing selection manager."""

        for entity in list(items):
            self.deselect(entity)
        return self.selected()

    def toggle(self, entity: Any) -> Any:
        """Toggle one entity in the current selection."""

        selection = self.selection()
        if selection is None:
            return None
        result = self._call_first(selection, ("toggle",), entity)
        if result is not None:
            return result
        if self.contains(entity):
            return self.deselect(entity)
        return self.select(entity)

    def clear(self) -> Any:
        """Clear the current selection."""

        selection = self.selection()
        if selection is None:
            return None
        return self._call_first(selection, ("clear",))

    def invert(self) -> list[Any]:
        """Invert selection over the current selectable workspace entities."""

        selection = self.selection()
        if selection is None:
            return []
        result = self._call_first(selection, ("invert",), self.workspace())
        if result is not None:
            return list(result)

        current = set(self.selected())
        targets = [entity for entity in self._selectable_entities() if entity not in current]
        self.select_many(targets)
        return self.selected()

    def select_all(self) -> list[Any]:
        """Select every selectable entity in the workspace."""

        targets = self._selectable_entities()
        self.select_many(targets)
        return self.selected()

    def bounding_box(self) -> Any:
        """Return a combined bounding box for the current selection when possible."""

        items = self.selected()
        if not items:
            return None

        first_box = getattr(items[0], "bounding_box", None)
        if first_box is None:
            return None

        bounds = self._clone_bounds(first_box)
        if bounds is None:
            return first_box

        for entity in items[1:]:
            box = getattr(entity, "bounding_box", None)
            if box is None:
                continue
            self._add_box(bounds, box)
        return bounds

    def filter(self, predicate: Callable[[Any], bool]) -> list[Any]:
        """Return selected entities that satisfy a predicate."""

        return [entity for entity in self.selected() if predicate(entity)]

    def find(self, predicate: Callable[[Any], bool]) -> Any:
        """Return the first selected entity that satisfies a predicate."""

        for entity in self.selected():
            if predicate(entity):
                return entity
        return None

    def _selectable_entities(self) -> list[Any]:
        """Return selectable workspace entities using existing workspace APIs."""

        workspace = self.workspace()
        selectable = getattr(workspace, "selectable_entities", None)
        if callable(selectable):
            return list(selectable())

        entities = getattr(workspace, "entities", None)
        if entities is None:
            return []
        return list(entities)

    def _clone_bounds(self, box: Any) -> Any:
        """Create a mutable copy of a bounding-box-like object."""

        copy_method = getattr(box, "copy", None)
        if callable(copy_method):
            return copy_method()

        box_type = type(box)
        try:
            clone = box_type()
        except TypeError:
            return None

        add_method = getattr(clone, "add", None)
        if callable(add_method):
            min_point = getattr(box, "min", None)
            max_point = getattr(box, "max", None)
            if min_point is not None:
                add_method(min_point)
            if max_point is not None:
                add_method(max_point)
            return clone
        return None

    def _add_box(self, bounds: Any, box: Any) -> None:
        """Add a bounding-box-like object into an existing bounds object."""

        add_box = getattr(bounds, "add_box", None)
        if callable(add_box):
            add_box(box)
            return

        add = getattr(bounds, "add", None)
        if callable(add):
            min_point = getattr(box, "min", None)
            max_point = getattr(box, "max", None)
            if min_point is not None:
                add(min_point)
            if max_point is not None:
                add(max_point)

    def _call_first(self, obj: Any, names: tuple[str, ...], *args: Any) -> Any:
        """Call the first available method from a list of names."""

        if obj is None:
            return None
        for name in names:
            method = getattr(obj, name, None)
            if callable(method):
                return method(*args)
        return None

    def _read_attr_or_call(self, obj: Any, names: tuple[str, ...]) -> Any:
        """Read the first available attribute or zero-argument method."""

        if obj is None:
            return None
        for name in names:
            if not hasattr(obj, name):
                continue
            value = getattr(obj, name)
            if callable(value):
                try:
                    return value()
                except TypeError:
                    continue
            return value
        return None

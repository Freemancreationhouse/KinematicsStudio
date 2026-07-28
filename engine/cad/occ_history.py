from copy import deepcopy


class OCCHistory:
    """Undo/Redo history for OpenCascade shape collections."""

    def __init__(self):

        self._undo = []

        self._redo = []

    # --------------------------------------------------

    def clear(self):

        self._undo.clear()

        self._redo.clear()

    # --------------------------------------------------

    def save(self, occ_manager):

        self._undo.append(
            deepcopy(occ_manager.shapes)
        )

        self._redo.clear()

    # --------------------------------------------------

    def can_undo(self):

        return len(self._undo) > 0

    # --------------------------------------------------

    def can_redo(self):

        return len(self._redo) > 0

    # --------------------------------------------------

    def undo(self, occ_manager):

        if not self.can_undo():
            return False

        self._redo.append(
            deepcopy(occ_manager.shapes)
        )

        occ_manager.clear()

        for shape in self._undo.pop():
            occ_manager.add(shape)

        return True

    # --------------------------------------------------

    def redo(self, occ_manager):

        if not self.can_redo():
            return False

        self._undo.append(
            deepcopy(occ_manager.shapes)
        )

        occ_manager.clear()

        for shape in self._redo.pop():
            occ_manager.add(shape)

        return True

    # --------------------------------------------------

    def snapshot(self, occ_manager):

        return deepcopy(occ_manager.shapes)

    # --------------------------------------------------

    def restore(
        self,
        occ_manager,
        snapshot,
    ):

        occ_manager.clear()

        for shape in deepcopy(snapshot):
            occ_manager.add(shape)

    # --------------------------------------------------

    @property
    def undo_count(self):

        return len(self._undo)

    # --------------------------------------------------

    @property
    def redo_count(self):

        return len(self._redo)
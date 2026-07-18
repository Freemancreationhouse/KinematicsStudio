import threading
import time
from pathlib import Path

from engine.storage.project import ProjectSerializer


class AutoSaveManager:
    """Background autosave and recovery-file coordinator."""

    def __init__(
        self,
        get_workspace,
        serializer=None,
        interval_seconds=300,
        recovery_path=None,
    ):

        self.get_workspace = get_workspace
        self.serializer = serializer or ProjectSerializer()
        self.interval_seconds = int(interval_seconds)
        self.recovery_path = Path(recovery_path or ".kinematics_recovery.ksproj")
        self.enabled = False
        self._stop_event = threading.Event()
        self._thread = None
        self.last_error = None

    # --------------------------------

    def configure(self, interval_seconds=None, recovery_path=None):
        """Update autosave settings without interrupting editing."""

        if interval_seconds is not None:
            self.interval_seconds = max(1, int(interval_seconds))

        if recovery_path is not None:
            self.recovery_path = Path(recovery_path)

    # --------------------------------

    def start(self):
        """Start background autosave."""

        if self.enabled:
            return

        self.enabled = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    # --------------------------------

    def stop(self):
        """Stop background autosave."""

        self.enabled = False
        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    # --------------------------------

    def autosave_now(self):
        """Write the current workspace to the recovery file."""

        workspace = self.get_workspace()

        if workspace is None:
            return None

        saved = self.serializer.save(
            workspace,
            self.recovery_path,
            settings={
                "autosave": True,
                "timestamp": time.time(),
            },
        )
        self.last_error = None

        return saved

    # --------------------------------

    def has_recovery(self):
        """Return True when a recovery file is available."""

        return self.recovery_path.exists()

    # --------------------------------

    def load_recovery(self):
        """Load the workspace from the recovery file."""

        if not self.has_recovery():
            return None

        return self.serializer.load(self.recovery_path)

    # --------------------------------

    def clear_recovery(self):
        """Remove the recovery file after successful save or recovery."""

        if self.recovery_path.exists():
            self.recovery_path.unlink()

    # --------------------------------

    def _run(self):

        while not self._stop_event.wait(self.interval_seconds):
            if not self.enabled:
                break

            try:
                self.autosave_now()
            except Exception as error:
                self.last_error = error

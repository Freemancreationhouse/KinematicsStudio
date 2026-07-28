from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4


class AIStudioError(RuntimeError):
    """Base error for production AI Studio runtime failures."""


class AIProviderNotConfiguredError(AIStudioError):
    """Raised when a task requires an AI provider but none is configured."""


class AITaskCancelledError(AIStudioError):
    """Raised when an AI task is cancelled before execution."""


def _timestamp():
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AITask:
    """Tracks one production AI task lifecycle."""

    prompt: str
    context: dict = field(default_factory=dict)
    provider_id: str = ""
    capability: str = "chat"
    id: str = field(default_factory=lambda: str(uuid4()))
    state: str = "Pending"
    progress: float = 0.0
    result: object = None
    error: str = ""
    created_at: str = field(default_factory=_timestamp)
    started_at: str = ""
    completed_at: str = ""
    cancelled: bool = False

    def to_dict(self):
        """Return JSON-safe task state."""

        return {
            "id": self.id,
            "prompt": self.prompt,
            "context": dict(self.context),
            "provider_id": self.provider_id,
            "capability": self.capability,
            "state": self.state,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "cancelled": self.cancelled,
        }

    @classmethod
    def from_dict(cls, data):
        """Restore task state from persisted data."""

        task = cls(
            data.get("prompt", ""),
            dict(data.get("context", {})),
            data.get("provider_id", ""),
            data.get("capability", "chat"),
            data.get("id") or str(uuid4()),
        )
        task.state = data.get("state", "Pending")
        task.progress = float(data.get("progress", 0.0))
        task.result = data.get("result")
        task.error = data.get("error", "")
        task.created_at = data.get("created_at", task.created_at)
        task.started_at = data.get("started_at", "")
        task.completed_at = data.get("completed_at", "")
        task.cancelled = bool(data.get("cancelled", False))
        return task


@dataclass
class AIRuntimeStatistics:
    """Production AI runtime statistics."""

    submitted: int = 0
    running: int = 0
    completed: int = 0
    failed: int = 0
    cancelled: int = 0
    queued: int = 0
    providers: int = 0
    total_runtime_ms: float = 0.0

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)


class AIRuntime:
    """Runs AI tasks through registered production providers."""

    def __init__(self, provider_registry, max_workers=2):
        self.provider_registry = provider_registry
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="AIStudio")
        self.tasks = {}
        self.futures = {}
        self.events = []
        self.on_change = None
        self.statistics = AIRuntimeStatistics()

    def submit(self, prompt, context=None, capability="chat", provider_id="", background=True):
        """Submit an AI task and return its task record."""

        task = AITask(prompt, dict(context or {}), provider_id, capability)
        self.tasks[task.id] = task
        self._record_event("task_submitted", task)
        if background:
            self.futures[task.id] = self.executor.submit(self._run_task, task)
        else:
            self._run_task(task)
        self._refresh_statistics()
        return task

    def cancel(self, task_id):
        """Cancel a pending/running AI task when possible."""

        task = self.tasks.get(task_id)
        if task is None:
            return False
        task.cancelled = True
        future = self.futures.get(task_id)
        if future is not None:
            future.cancel()
        if task.state in ("Pending", "Running"):
            task.state = "Cancelled"
            task.completed_at = _timestamp()
            task.progress = 0.0
            self._record_event("task_cancelled", task)
            self._refresh_statistics()
        return True

    def result(self, task_id, timeout=None):
        """Return a task result, waiting for background completion if needed."""

        future = self.futures.get(task_id)
        if future is not None:
            future.result(timeout=timeout)
        task = self.tasks.get(task_id)
        if task is None:
            return None
        if task.error:
            raise AIStudioError(task.error)
        return task.result

    def task_for(self, task_id):
        """Return a task by ID."""

        return self.tasks.get(task_id)

    def shutdown(self, wait=False):
        """Stop accepting background work and release runtime resources."""

        self.executor.shutdown(wait=wait, cancel_futures=True)

    def to_dict(self):
        """Return JSON-safe runtime state."""

        return {
            "tasks": [task.to_dict() for task in self.tasks.values()],
            "events": list(self.events),
            "statistics": self.statistics.to_dict(),
        }

    def from_dict(self, data):
        """Restore persisted completed task/session metadata."""

        self.tasks = {
            task.id: task for task in [
                AITask.from_dict(item) for item in data.get("tasks", [])
            ]
        }
        self.futures.clear()
        self.events = list(data.get("events", []))
        self._refresh_statistics()

    def _run_task(self, task):
        started = perf_counter()
        try:
            if task.cancelled:
                raise AITaskCancelledError("AI task was cancelled before execution.")
            provider = self.provider_registry.provider_for(task.provider_id, task.capability)
            task.provider_id = provider.provider_id
            task.state = "Running"
            task.started_at = _timestamp()
            task.progress = 0.05
            self._record_event("task_started", task)
            task.result = provider.execute(task, self._progress_for(task))
            task.progress = 1.0
            task.state = "Completed"
            task.completed_at = _timestamp()
            self._record_event("task_completed", task)
            return task.result
        except Exception as exc:
            task.state = "Cancelled" if isinstance(exc, AITaskCancelledError) else "Failed"
            task.error = str(exc)
            task.completed_at = _timestamp()
            self._record_event("task_failed", task)
            if isinstance(exc, AIProviderNotConfiguredError):
                raise
            return None
        finally:
            elapsed_ms = (perf_counter() - started) * 1000.0
            self.statistics.total_runtime_ms += elapsed_ms
            self._refresh_statistics()

    def _progress_for(self, task):
        def update(progress, message=""):
            task.progress = max(0.0, min(float(progress), 1.0))
            self._record_event("task_progress", task, message)
        return update

    def _record_event(self, event_type, task, message=""):
        event = {
            "type": event_type,
            "task_id": task.id,
            "state": task.state,
            "progress": task.progress,
            "message": message,
            "timestamp": _timestamp(),
        }
        self.events.append(event)
        if self.on_change is not None:
            self.on_change(event)

    def _refresh_statistics(self):
        states = [task.state for task in self.tasks.values()]
        self.statistics.submitted = len(self.tasks)
        self.statistics.running = states.count("Running")
        self.statistics.completed = states.count("Completed")
        self.statistics.failed = states.count("Failed")
        self.statistics.cancelled = states.count("Cancelled")
        self.statistics.queued = states.count("Pending")
        self.statistics.providers = len(self.provider_registry.providers)
        return self.statistics

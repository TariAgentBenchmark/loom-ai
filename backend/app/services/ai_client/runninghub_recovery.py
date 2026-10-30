"""Per-application-task checkpoints; never shared between concurrent users."""
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from app.services.ai_client.exceptions import AIClientException

RUNNINGHUB_CHECKPOINT_KEY = "runninghubWorkflows"


class RunningHubPendingError(AIClientException):
    """A submitted job still needs polling, not a new paid submission."""


@dataclass
class RunningHubRecovery:
    tasks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    save: Optional[Callable[[Dict[str, Dict[str, Any]]], None]] = None

    def checkpoint(self, key: str, record: Dict[str, Any]) -> None:
        self.tasks[key] = dict(record)
        if self.save:
            self.save(self.tasks)


runninghub_recovery: ContextVar[Optional[RunningHubRecovery]] = ContextVar(
    "runninghub_recovery", default=None,
)

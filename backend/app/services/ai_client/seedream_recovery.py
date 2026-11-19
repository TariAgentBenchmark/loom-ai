"""Task-local, durable Seedream job IDs and completed companion branches."""

from collections.abc import Callable
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from app.services.ai_client.exceptions import AIClientException

SEEDREAM_STATE_KEY = "seedreamState"


class SeedreamPendingError(AIClientException):
    """An accepted, queryable job is pending; only poll its existing task ID."""


class SeedreamSubmissionUnknownError(AIClientException):
    """A POST may have been accepted without a job ID. Never auto-resubmit."""


@dataclass
class SeedreamRecovery:
    records: dict[str, dict[str, Any]] = field(default_factory=dict)
    save: Callable[[dict[str, dict[str, Any]]], None] | None = None

    def checkpoint(self, slot: str, record: dict[str, Any]) -> None:
        self.records[slot] = dict(record)
        if self.save:
            self.save(self.records)


seedream_recovery: ContextVar[SeedreamRecovery | None] = ContextVar(
    "seedream_recovery",
    default=None,
)

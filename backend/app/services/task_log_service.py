import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.task_log import TaskLog, TaskLogLevel

logger = logging.getLogger(__name__)


class TaskLogService:
    """Persist structured logs tied to a specific task."""

    def __init__(self) -> None:
        self._max_text = 4000
        self._max_depth = 3
        self._max_items = 50

    def _truncate_text(self, value: str) -> str:
        if len(value) <= self._max_text:
            return value
        return f"{value[: self._max_text]}...(truncated)"

    def _sanitize_value(self, value: Any, depth: int = 0) -> Any:
        if depth >= self._max_depth:
            return "<max-depth>"

        if isinstance(value, (bytes, bytearray)):
            return f"<{len(value)} bytes>"

        if isinstance(value, str):
            return self._truncate_text(value)

        if isinstance(value, dict):
            sanitized: Dict[str, Any] = {}
            for idx, (key, item) in enumerate(value.items()):
                if idx >= self._max_items:
                    sanitized["<truncated>"] = f"+{len(value) - self._max_items} keys"
                    break
                sanitized[str(key)] = self._sanitize_value(item, depth + 1)
            return sanitized

        if isinstance(value, (list, tuple, set)):
            items = list(value)
            sanitized_items = [
                self._sanitize_value(item, depth + 1)
                for item in items[: self._max_items]
            ]
            if len(items) > self._max_items:
                sanitized_items.append(f"<+{len(items) - self._max_items} items>")
            return sanitized_items

        try:
            return value
        except Exception:  # pragma: no cover - defensive
            return repr(value)

    def _sanitize_details(self, details: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not details:
            return None
        if not isinstance(details, dict):
            return {"value": self._sanitize_value(details)}
        return self._sanitize_value(details)  # type: ignore[return-value]

    def record(
        self,
        db: Session,
        task: Task,
        *,
        event: str,
        message: str,
        level: str = TaskLogLevel.INFO.value,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a log entry without letting logging failures break task flow."""
        try:
            level_value = (level or TaskLogLevel.INFO.value).lower()
            if level_value not in {lvl.value for lvl in TaskLogLevel}:
                level_value = TaskLogLevel.INFO.value

            log_entry = TaskLog(
                task_id=task.id,
                task_task_id=task.task_id,
                level=level_value,
                event=(event or "event").strip()[:100],
                message=self._truncate_text(message or ""),
                details=self._sanitize_details(details),
            )
            db.add(log_entry)
            db.flush()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "Failed to record task log for %s (%s): %s",
                getattr(task, "task_id", "<unknown>"),
                event,
                exc,
            )


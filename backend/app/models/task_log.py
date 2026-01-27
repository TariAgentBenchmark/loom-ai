from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class TaskLogLevel(PyEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class TaskLog(Base):
    """Structured per-task log entries for admin debugging."""

    __tablename__ = "task_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    task_task_id = Column(String(50), nullable=False, index=True)

    level = Column(String(10), nullable=False, default=TaskLogLevel.INFO.value, index=True)
    event = Column(String(100), nullable=False, index=True)
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    task = relationship("Task", back_populates="logs")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return (
            f"<TaskLog(id={self.id}, task_task_id={self.task_task_id}, "
            f"level={self.level}, event={self.event})>"
        )


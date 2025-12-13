from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric
from sqlalchemy.sql import func

from app.core.database import Base


class AgentCommissionStatus:
    UNSETTLED = "unsettled"
    SETTLED = "settled"


class AgentCommission(Base):
    __tablename__ = "agent_commissions"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # cents
    rate = Column(Numeric(5, 4), nullable=False)  # effective rate
    status = Column(String(20), default=AgentCommissionStatus.UNSETTLED, index=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    settled_at = Column(DateTime(timezone=True), nullable=True)
    settled_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

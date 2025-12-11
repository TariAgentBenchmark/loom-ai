from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AgentStatus(PyEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class InvitationCodeStatus(PyEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    EXPIRED = "expired"


class Agent(Base):
    """代理商模型"""

    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # 绑定的管理用户
    parent_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True, index=True)  # 上级代理商
    level = Column(Integer, default=1)  # 代理层级，1=一级，2=二级
    contact = Column(String(100), nullable=True)  # 负责人/联系方式
    notes = Column(String(500), nullable=True)
    status = Column(Enum(AgentStatus), default=AgentStatus.ACTIVE)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    invitation_codes = relationship(
        "InvitationCode",
        back_populates="agent",
        cascade="all, delete-orphan",
    )
    users = relationship(
        "User",
        back_populates="agent",
        foreign_keys="User.agent_id",
    )
    owner_user = relationship(
        "User",
        back_populates="managed_agent",
        foreign_keys=[owner_user_id],
    )
    parent = relationship(
        "Agent",
        remote_side=[id],
        back_populates="children",
        foreign_keys=[parent_agent_id],
    )
    children = relationship(
        "Agent",
        back_populates="parent",
        foreign_keys=[parent_agent_id],
    )

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name={self.name})>"


class InvitationCode(Base):
    """邀请码模型"""

    __tablename__ = "invitation_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    description = Column(String(255), nullable=True)
    max_uses = Column(Integer, nullable=True)  # None 或 0 表示不限
    usage_count = Column(Integer, default=0)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(InvitationCodeStatus), default=InvitationCodeStatus.ACTIVE)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    agent = relationship("Agent", back_populates="invitation_codes")
    users = relationship("User", back_populates="invitation_code")

    def __repr__(self) -> str:
        return (
            f"<InvitationCode(id={self.id}, code={self.code}, agent_id={self.agent_id})>"
        )

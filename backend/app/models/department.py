from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, TIMESTAMP, ForeignKey, func, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, TEXT
from typing import Optional

from app.db.base_class import Base

class Department(Base):
    __tablename__ = "departments"

    id: Mapped[uuid4] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[uuid4] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)
    icon: Mapped[str] = mapped_column(String(10), default="📁", nullable=False)
    
    config: Mapped[dict] = mapped_column(JSONB, default={}, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="departments")
    members: Mapped[list["DepartmentMember"]] = relationship(back_populates="department", cascade="all, delete-orphan")
    knowledge_docs: Mapped[list["KnowledgeDoc"]] = relationship(back_populates="department", cascade="all, delete-orphan")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="department", cascade="all, delete-orphan")


class DepartmentMember(Base):
    __tablename__ = "department_members"

    id: Mapped[uuid4] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    department_id: Mapped[uuid4] = mapped_column(ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid4] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id: Mapped[uuid4] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    role: Mapped[str] = mapped_column(String(50), default="member", nullable=False)  # lead, approver, member, viewer
    
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    department: Mapped["Department"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="memberships")

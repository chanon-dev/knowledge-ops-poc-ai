from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, String, TIMESTAMP, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TEXT, JSONB

from app.db.base_class import Base


class TrainingMethod(Base):
    __tablename__ = "training_methods"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_training_methods_tenant_name"),
    )

    id: Mapped[uuid4] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[uuid4] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    method_key: Mapped[str] = mapped_column(String(50), nullable=False)  # registry lookup: "lora", "qlora", etc.
    description: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)
    default_config: Mapped[dict] = mapped_column(JSONB, default={}, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped["Tenant"] = relationship()

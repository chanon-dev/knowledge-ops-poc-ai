from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, String, TIMESTAMP, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.db.base_class import Base


class AllowedModel(Base):
    __tablename__ = "allowed_models"
    __table_args__ = (
        UniqueConstraint("tenant_id", "model_name", name="uq_allowed_models_tenant_model"),
    )

    id: Mapped[uuid4] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[uuid4] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    provider_id: Mapped[Optional[uuid4]] = mapped_column(ForeignKey("ai_providers.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped["Tenant"] = relationship()
    provider: Mapped[Optional["AIProvider"]] = relationship()

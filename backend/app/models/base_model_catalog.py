from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, Float, String, TIMESTAMP, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from app.db.base_class import Base


class BaseModelCatalog(Base):
    __tablename__ = "base_model_catalog"
    __table_args__ = (
        UniqueConstraint("tenant_id", "model_name", name="uq_base_model_catalog_tenant_model"),
    )

    id: Mapped[uuid4] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[uuid4] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)  # HF model ID
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    size_billion: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # param count in billions
    recommended_ram_gb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    default_target_modules: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # ["q_proj", "v_proj", ...]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped["Tenant"] = relationship()

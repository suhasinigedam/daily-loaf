from datetime import datetime

from sqlalchemy import DateTime, Identity, String, Text, true
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base


class Customer(AuditMixin, Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())
    anonymised_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
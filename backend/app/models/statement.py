from datetime import date, datetime

from sqlalchemy import DateTime, ForeignKey, Identity, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import StatementStatus
from app.models.base import AuditMixin, Base, pg_enum


class MonthlyStatement(AuditMixin, Base):
    __tablename__ = "monthly_statements"
    __table_args__ = (UniqueConstraint("customer_id", "month"),)

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    month: Mapped[date]
    opening_cents: Mapped[int]
    orders_cents: Mapped[int]
    payments_cents: Mapped[int]
    adjustments_cents: Mapped[int]
    closing_cents: Mapped[int]
    status: Mapped[StatementStatus] = mapped_column(
        pg_enum(StatementStatus, "statement_status"), default=StatementStatus.DRAFT
    )
    pdf_s3_key: Mapped[str | None] = mapped_column(String(200))
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class BillingMonth(Base):
    __tablename__ = "billing_months"

    month: Mapped[date] = mapped_column(primary_key=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    generated_by: Mapped[str] = mapped_column(String(100))
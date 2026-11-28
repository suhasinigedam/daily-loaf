"""Base class for all tables, plus audit columns (who changed what, when)."""

from datetime import datetime
from enum import StrEnum
from sqlalchemy import DateTime, MetaData, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Predictable names for constraints, so Alembic migrations stay stable.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class AuditMixin:
    """Adds created/updated time and user to a table."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[str] = mapped_column(String(100))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    updated_by: Mapped[str] = mapped_column(String(100))


def touch(obj: AuditMixin, username: str) -> None:
    """Record who created or last changed a row."""
    obj.updated_by = username
    if getattr(obj, "created_by", None) is None:
        obj.created_by = username
        
def _enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [member.value for member in enum_cls]


def pg_enum(enum_cls: type[StrEnum], name: str) -> SAEnum:
    """A native Postgres enum that stores the lowercase values ("pending")."""
    return SAEnum(enum_cls, name=name, values_callable=_enum_values)
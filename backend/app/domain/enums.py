"""Fixed lists of allowed values, shared by the database and the API."""

from enum import StrEnum


class OrderStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PREP = "in_prep"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderSource(StrEnum):
    WHATSAPP = "whatsapp"
    PHONE = "phone"
    OTHER = "other"


class PaymentMethod(StrEnum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    OTHER = "other"


class StatementStatus(StrEnum):
    DRAFT = "draft"
    ISSUED = "issued"
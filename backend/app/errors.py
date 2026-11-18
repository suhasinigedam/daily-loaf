from enum import StrEnum


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    NOT_FOUND = "NOT_FOUND"
    NO_RATE_FOR_DATE = "NO_RATE_FOR_DATE"
    INVALID_STATUS_TRANSITION = "INVALID_STATUS_TRANSITION"
    ORDER_NOT_EDITABLE = "ORDER_NOT_EDITABLE"
    CUSTOMER_INACTIVE = "CUSTOMER_INACTIVE"
    PERIOD_LOCKED = "PERIOD_LOCKED"
    RATE_EXISTS = "RATE_EXISTS"
    PREVIOUS_MONTH_NOT_ISSUED = "PREVIOUS_MONTH_NOT_ISSUED"
    LATER_MONTH_GENERATED = "LATER_MONTH_GENERATED"
    MONTH_NOT_ENDED = "MONTH_NOT_ENDED"
    STATEMENT_ALREADY_ISSUED = "STATEMENT_ALREADY_ISSUED"
    STATEMENT_NOT_ISSUED = "STATEMENT_NOT_ISSUED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


HTTP_STATUS: dict[ErrorCode, int] = {
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.NO_RATE_FOR_DATE: 422,
    ErrorCode.INVALID_STATUS_TRANSITION: 409,
    ErrorCode.ORDER_NOT_EDITABLE: 409,
    ErrorCode.CUSTOMER_INACTIVE: 409,
    ErrorCode.PERIOD_LOCKED: 409,
    ErrorCode.RATE_EXISTS: 409,
    ErrorCode.PREVIOUS_MONTH_NOT_ISSUED: 409,
    ErrorCode.LATER_MONTH_GENERATED: 409,
    ErrorCode.MONTH_NOT_ENDED: 409,
    ErrorCode.STATEMENT_ALREADY_ISSUED: 409,
    ErrorCode.STATEMENT_NOT_ISSUED: 409,
    ErrorCode.INTERNAL_ERROR: 500,
}


class DomainError(Exception):
    """A business-rule violation the user can understand and fix."""

    def __init__(self, code: ErrorCode, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.field = field

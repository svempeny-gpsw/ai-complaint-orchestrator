from enum import Enum


class ComplaintCategory(str, Enum):
    BILLING = "billing"
    DELIVERY = "delivery"
    ACCOUNT = "account"
    PRODUCT = "product"
    SERVICE = "service"
    OTHER = "other"


class ComplaintPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ComplaintSubcategory(str, Enum):
    DUPLICATE_CHARGE = "duplicate_charge"
    CHARGE_AFTER_CANCELLATION = "charge_after_cancellation"
    REFUND_NOT_RECEIVED = "refund_not_received"
    DELIVERY_DELAY = "delivery_delay"
    MISSING_DELIVERY = "missing_delivery"
    ACCOUNT_ACCESS = "account_access"
    PRODUCT_ISSUE = "product_issue"
    SERVICE_ISSUE = "service_issue"
    OTHER = "other"


class ProcessingRoute(str, Enum):
    DETERMINISTIC = "deterministic"
    LLM = "llm"


class ComplaintChannel(str, Enum):
    ONLINE = "online"
    PHONE = "phone"


class ComplaintStatus(str, Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    PROCESSED = "processed"
    NEEDS_INFORMATION = "needs_information"
    FAILED = "failed"


class WorkflowDispatchStatus(str, Enum):
    NOT_REQUESTED = "not_requested"
    PENDING = "pending"
    DISPATCHED = "dispatched"
    FAILED = "failed"

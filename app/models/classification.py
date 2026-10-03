from enum import Enum
from pydantic import BaseModel, Field


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


class ComplaintClassification(BaseModel):
    category: ComplaintCategory
    subcategory: ComplaintSubcategory
    priority: ComplaintPriority

    customer_intent: str = Field(
        description="What outcome the customer appears to be seeking"
    )

    summary: str = Field(
        description="Short factual summary of the complaint"
    )
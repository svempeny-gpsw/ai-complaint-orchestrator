from datetime import datetime, timezone
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


class ProcessingRoute(str, Enum):
    DETERMINISTIC = "deterministic"
    LLM = "llm"


class ComplaintChannel(str, Enum):
    ONLINE = "online"
    PHONE = "phone"


class ComplaintStatus(str, Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    RESOLVED = "resolved"
    FAILED = "failed"


class ComplaintCreate(BaseModel):
    customer_id: str = Field(min_length=1)
    channel: ComplaintChannel
    complaint_text: str = Field(min_length=10)


class ComplaintResponse(BaseModel):
    complaint_id: str
    customer_id: str
    channel: ComplaintChannel
    complaint_text: str
    status: ComplaintStatus

    processing_route: str | None = None
    category: str | None = None
    subcategory: str | None = None
    priority: str | None = None
    customer_intent: str | None = None
    summary: str | None = None
    model_used: str | None = None

    created_at: datetime
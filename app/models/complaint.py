from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import (
    ComplaintCategory,
    ComplaintChannel,
    ComplaintPriority,
    ComplaintStatus,
    ComplaintSubcategory,
    ProcessingRoute,
    WorkflowDispatchStatus,
)


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
    workflow_dispatch_status: WorkflowDispatchStatus

    processing_route: ProcessingRoute | None = None
    category: ComplaintCategory | None = None
    subcategory: ComplaintSubcategory | None = None
    priority: ComplaintPriority | None = None
    customer_intent: str | None = None
    summary: str | None = None
    model_used: str | None = None

    created_at: datetime

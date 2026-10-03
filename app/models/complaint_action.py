from datetime import datetime

from pydantic import BaseModel, Field


class ComplaintActionCreate(BaseModel):
    action: str = Field(min_length=1, max_length=100)
    action_status: str = Field(min_length=1, max_length=30)
    reason: str = Field(min_length=1)


class ComplaintActionResponse(BaseModel):
    action_id: str
    complaint_id: str
    action: str
    action_status: str
    reason: str
    created_at: datetime
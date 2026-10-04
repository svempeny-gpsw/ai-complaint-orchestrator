from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ComplaintActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ComplaintActionResponse(BaseModel):
    action_id: str
    complaint_id: str
    action: str
    action_status: str
    reason: str
    created_at: datetime

from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.complaint import (
    ComplaintCreate,
    ComplaintResponse,
)
from app.models.complaint_db import ComplaintDB
from app.services.processing_service import process_complaint


def create_complaint(
    db: Session,
    complaint: ComplaintCreate,
) -> ComplaintResponse:

    # First persist the raw complaint.
    db_complaint = ComplaintDB(
        complaint_id=f"CMP-{uuid4().hex[:8].upper()}",
        customer_id=complaint.customer_id,
        channel=complaint.channel.value,
        complaint_text=complaint.complaint_text,
        status="received",
    )

    db.add(db_complaint)
    db.commit()
    db.refresh(db_complaint)

    # Then classify/process it.
    process_complaint(db, db_complaint)

    return ComplaintResponse.model_validate(
        db_complaint,
        from_attributes=True,
    )


def get_complaint(
    db: Session,
    complaint_id: str,
) -> ComplaintResponse | None:

    complaint = db.get(ComplaintDB, complaint_id)

    if complaint is None:
        return None

    return ComplaintResponse.model_validate(
        complaint,
        from_attributes=True,
    )
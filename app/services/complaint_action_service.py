from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.complaint_action import (
    ComplaintActionCreate,
    ComplaintActionResponse,
)
from app.models.complaint_action_db import ComplaintActionDB
from app.models.complaint_db import ComplaintDB


def create_complaint_action(
    db: Session,
    complaint_id: str,
    action: ComplaintActionCreate,
) -> ComplaintActionResponse:

    # Make sure the complaint exists.
    complaint = db.get(ComplaintDB, complaint_id)

    if complaint is None:
        raise ValueError("Complaint not found")

    # Idempotency check:
    # if this action already exists for this complaint,
    # return the existing record instead of creating another one.
    existing_action = db.scalar(
        select(ComplaintActionDB).where(
            ComplaintActionDB.complaint_id == complaint_id,
            ComplaintActionDB.action == action.action,
        )
    )

    if existing_action is not None:
        return ComplaintActionResponse.model_validate(
            existing_action,
            from_attributes=True,
        )

    db_action = ComplaintActionDB(
        action_id=f"ACT-{uuid4().hex[:8].upper()}",
        complaint_id=complaint_id,
        action=action.action,
        action_status=action.action_status,
        reason=action.reason,
    )

    db.add(db_action)
    db.commit()
    db.refresh(db_action)

    return ComplaintActionResponse.model_validate(
        db_action,
        from_attributes=True,
    )


def get_complaint_actions(
    db: Session,
    complaint_id: str,
) -> list[ComplaintActionResponse]:

    actions = db.scalars(
        select(ComplaintActionDB)
        .where(
            ComplaintActionDB.complaint_id == complaint_id
        )
        .order_by(ComplaintActionDB.created_at.asc())
    ).all()

    return [
        ComplaintActionResponse.model_validate(
            action,
            from_attributes=True,
        )
        for action in actions
    ]
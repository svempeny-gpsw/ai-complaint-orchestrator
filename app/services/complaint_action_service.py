from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.complaint_action import (
    ComplaintActionResponse,
)
from app.models.complaint_action_db import ComplaintActionDB
from app.models.complaint_db import ComplaintDB
from app.services.complaint_action_policy import determine_permitted_action


class ComplaintNotFoundError(ValueError):
    pass


class ComplaintActionNotPermittedError(ValueError):
    pass


def create_complaint_action(
    db: Session,
    complaint_id: str,
) -> ComplaintActionResponse:

    # Make sure the complaint exists.
    complaint = db.get(ComplaintDB, complaint_id)

    if complaint is None:
        raise ComplaintNotFoundError("Complaint not found")

    permitted_action = determine_permitted_action(complaint)

    if permitted_action is None:
        raise ComplaintActionNotPermittedError(
            "Complaint classification does not permit an automated action"
        )

    # Idempotency check:
    # if this action already exists for this complaint,
    # return the existing record instead of creating another one.
    existing_action = db.scalar(
        select(ComplaintActionDB).where(
            ComplaintActionDB.complaint_id == complaint_id,
            ComplaintActionDB.action == permitted_action.action,
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
        action=permitted_action.action,
        action_status=permitted_action.action_status,
        reason=permitted_action.reason,
    )

    db.add(db_action)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing_action = db.scalar(
            select(ComplaintActionDB).where(
                ComplaintActionDB.complaint_id == complaint_id,
                ComplaintActionDB.action == permitted_action.action,
            )
        )
        if existing_action is None:
            raise

        return ComplaintActionResponse.model_validate(
            existing_action,
            from_attributes=True,
        )

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

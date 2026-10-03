from app.models.complaint import ComplaintChannel
from app.models.complaint_action import ComplaintActionCreate
from app.models.complaint_db import ComplaintDB
from app.services.complaint_action_service import create_complaint_action
from sqlalchemy import func, select
from app.models.complaint_action_db import ComplaintActionDB

def test_duplicate_action_returns_existing_action(db_session):
    complaint = ComplaintDB(
        complaint_id="CMP-IDEMPOTENT",
        customer_id="CUST-TEST",
        channel=ComplaintChannel.ONLINE.value,
        complaint_text="I have a duplicate charge on my account.",
        status="resolved",
    )

    db_session.add(complaint)
    db_session.commit()

    action_request = ComplaintActionCreate(
        action="initiate_duplicate_charge_refund",
        action_status="approved",
        reason="Duplicate charge matched deterministic refund policy",
    )

    first_action = create_complaint_action(
        db=db_session,
        complaint_id=complaint.complaint_id,
        action=action_request,
    )

    second_action = create_complaint_action(
        db=db_session,
        complaint_id=complaint.complaint_id,
        action=action_request,
    )

    action_count = db_session.scalar(
        select(func.count())
        .select_from(ComplaintActionDB)
        .where(
            ComplaintActionDB.complaint_id == complaint.complaint_id,
            ComplaintActionDB.action == action_request.action,
        )
    )

    assert action_count == 1
    assert first_action.action_id == second_action.action_id
    assert first_action.complaint_id == second_action.complaint_id
    assert first_action.action == second_action.action
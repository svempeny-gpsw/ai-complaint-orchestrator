from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.api.complaints import router
from app.core.database import get_db
from app.models.complaint_action_db import ComplaintActionDB
from app.models.complaint_db import ComplaintDB
from app.services.complaint_action_service import (
    ComplaintActionNotPermittedError,
    create_complaint_action,
)


def _persist_complaint(
    db_session,
    *,
    complaint_id: str,
    category: str,
    subcategory: str,
) -> ComplaintDB:
    complaint = ComplaintDB(
        complaint_id=complaint_id,
        customer_id="CUST-TEST",
        channel="online",
        complaint_text="A sufficiently detailed complaint.",
        status="processed",
        workflow_dispatch_status="dispatched",
        category=category,
        subcategory=subcategory,
    )
    db_session.add(complaint)
    db_session.commit()
    return complaint


def _build_test_client(db_session) -> TestClient:
    app = FastAPI()
    app.include_router(router)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_duplicate_charge_derives_initiated_refund_review(db_session):
    complaint = _persist_complaint(
        db_session,
        complaint_id="CMP-DUPLICATE",
        category="billing",
        subcategory="duplicate_charge",
    )

    action = create_complaint_action(db_session, complaint.complaint_id)

    assert action.action == "initiate_duplicate_charge_refund"
    assert action.action_status == "initiated"
    assert action.action_status != "approved"
    assert (
        action.reason
        == "Duplicate charge classification initiated refund eligibility review"
    )


def test_charge_after_cancellation_derives_investigation(db_session):
    complaint = _persist_complaint(
        db_session,
        complaint_id="CMP-CANCELLATION",
        category="billing",
        subcategory="charge_after_cancellation",
    )

    action = create_complaint_action(db_session, complaint.complaint_id)

    assert action.action == "investigate_post_cancellation_charge"
    assert action.action_status == "initiated"


def test_unsupported_classification_cannot_create_action(db_session):
    complaint = _persist_complaint(
        db_session,
        complaint_id="CMP-UNSUPPORTED",
        category="delivery",
        subcategory="missing_delivery",
    )

    with pytest.raises(ComplaintActionNotPermittedError):
        create_complaint_action(db_session, complaint.complaint_id)

    action_count = db_session.scalar(
        select(func.count()).select_from(ComplaintActionDB)
    )
    assert action_count == 0


def test_needs_information_complaint_cannot_create_action(db_session):
    complaint = ComplaintDB(
        complaint_id="CMP-NEEDS-INFO",
        customer_id="CUST-TEST",
        channel="online",
        complaint_text="nothing happened",
        status="needs_information",
        workflow_dispatch_status="not_requested",
        category="billing",
        subcategory="duplicate_charge",
    )
    db_session.add(complaint)
    db_session.commit()

    with pytest.raises(ComplaintActionNotPermittedError):
        create_complaint_action(db_session, complaint.complaint_id)

    action_count = db_session.scalar(
        select(func.count()).select_from(ComplaintActionDB)
    )
    assert action_count == 0


def test_api_empty_object_returns_server_derived_action(db_session):
    complaint = _persist_complaint(
        db_session,
        complaint_id="CMP-API-SUPPORTED",
        category="billing",
        subcategory="duplicate_charge",
    )

    with _build_test_client(db_session) as client:
        response = client.post(
            f"/complaints/{complaint.complaint_id}/actions",
            json={},
        )

    assert response.status_code == 200
    assert response.json()["action"] == "initiate_duplicate_charge_refund"
    assert response.json()["action_status"] == "initiated"


def test_api_omitted_body_uses_empty_trigger_contract(db_session):
    complaint = _persist_complaint(
        db_session,
        complaint_id="CMP-API-NO-BODY",
        category="billing",
        subcategory="charge_after_cancellation",
    )

    with _build_test_client(db_session) as client:
        response = client.post(
            f"/complaints/{complaint.complaint_id}/actions"
        )

    assert response.status_code == 200
    assert response.json()["action"] == (
        "investigate_post_cancellation_charge"
    )
    assert response.json()["action_status"] == "initiated"


def test_api_rejects_client_supplied_action_and_status(db_session):
    complaint = _persist_complaint(
        db_session,
        complaint_id="CMP-MANUFACTURED",
        category="billing",
        subcategory="duplicate_charge",
    )

    with _build_test_client(db_session) as client:
        response = client.post(
            f"/complaints/{complaint.complaint_id}/actions",
            json={
                "action": "initiate_duplicate_charge_refund",
                "action_status": "approved",
                "reason": "caller supplied",
            },
        )

    action_count = db_session.scalar(
        select(func.count()).select_from(ComplaintActionDB)
    )
    assert response.status_code == 422
    assert action_count == 0


def test_api_unsupported_classification_returns_422(db_session):
    complaint = _persist_complaint(
        db_session,
        complaint_id="CMP-API-UNSUPPORTED",
        category="delivery",
        subcategory="missing_delivery",
    )

    with _build_test_client(db_session) as client:
        response = client.post(
            f"/complaints/{complaint.complaint_id}/actions",
            json={},
        )

    action_count = db_session.scalar(
        select(func.count()).select_from(ComplaintActionDB)
    )
    assert response.status_code == 422
    assert action_count == 0


def test_duplicate_action_returns_existing_action(db_session):
    complaint = _persist_complaint(
        db_session,
        complaint_id="CMP-IDEMPOTENT",
        category="billing",
        subcategory="duplicate_charge",
    )

    first_action = create_complaint_action(db_session, complaint.complaint_id)
    second_action = create_complaint_action(db_session, complaint.complaint_id)

    action_count = db_session.scalar(
        select(func.count())
        .select_from(ComplaintActionDB)
        .where(
            ComplaintActionDB.complaint_id == complaint.complaint_id,
            ComplaintActionDB.action == first_action.action,
        )
    )

    assert action_count == 1
    assert first_action.action_id == second_action.action_id


def test_uniqueness_race_returns_winning_action():
    db = Mock()
    complaint = ComplaintDB(
        complaint_id="CMP-RACE",
        customer_id="CUST-TEST",
        channel="online",
        complaint_text="I have a duplicate charge.",
        status="processed",
        workflow_dispatch_status="dispatched",
        category="billing",
        subcategory="duplicate_charge",
    )
    winning_action = ComplaintActionDB(
        action_id="ACT-WINNER",
        complaint_id=complaint.complaint_id,
        action="initiate_duplicate_charge_refund",
        action_status="initiated",
        reason=(
            "Duplicate charge classification initiated refund "
            "eligibility review"
        ),
        created_at=datetime.now(timezone.utc),
    )
    db.get.return_value = complaint
    db.scalar.side_effect = [None, winning_action]
    db.commit.side_effect = IntegrityError(
        "INSERT",
        {},
        Exception("unique constraint violation"),
    )

    result = create_complaint_action(db, complaint.complaint_id)

    db.rollback.assert_called_once_with()
    assert result.action_id == "ACT-WINNER"
    assert result.action_status == "initiated"

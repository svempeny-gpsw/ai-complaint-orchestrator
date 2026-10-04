import pytest
from unittest.mock import Mock, patch

from app.models.classification import ComplaintClassification
from app.models.enums import (
    ComplaintCategory,
    ComplaintPriority,
    ComplaintSubcategory,
)
from app.models.complaint_db import ComplaintDB
from app.services.processing_service import process_complaint


@patch("app.services.processing_service.trigger_complaint_workflow")
@patch("app.services.processing_service.classify_complaint")
def test_deterministic_complaint_does_not_call_llm(
    mock_classify,
    mock_trigger_workflow,
):
    db = Mock()

    complaint = ComplaintDB(
        complaint_id="CMP-TEST001",
        customer_id="CUST-TEST001",
        channel="online",
        complaint_text="I have a duplicate charge on my account.",
        status="received",
    )

    process_complaint(db, complaint)

    mock_classify.assert_not_called()

    assert complaint.processing_route == "deterministic"
    assert complaint.category == "billing"
    assert complaint.subcategory == "duplicate_charge"
    assert complaint.priority == "high"
    assert complaint.summary == "Customer reports a duplicate charge."
    assert complaint.status == "processed"
    assert complaint.workflow_dispatch_status == "dispatched"

    mock_trigger_workflow.assert_called_once_with(
        complaint_id="CMP-TEST001",
        category="billing",
        subcategory="duplicate_charge",
        priority="high",
        processing_route="deterministic",
    )


@patch("app.services.processing_service.trigger_complaint_workflow")
@patch("app.services.processing_service.classify_complaint")
def test_ambiguous_complaint_calls_llm(
    mock_classify,
    mock_trigger_workflow,
):
    db = Mock()

    mock_classify.return_value = ComplaintClassification(
        sufficient_information=True,
        category=ComplaintCategory.BILLING,
        subcategory=ComplaintSubcategory.CHARGE_AFTER_CANCELLATION,
        priority=ComplaintPriority.HIGH,
        customer_intent="Resolve unexpected charge after cancellation",
        summary="Customer was charged after cancelling their subscription.",
    )

    complaint = ComplaintDB(
        complaint_id="CMP-TEST002",
        customer_id="CUST-TEST002",
        channel="online",
        complaint_text=(
            "I cancelled last week but you have taken money "
            "from me again today."
        ),
        status="received",
    )

    process_complaint(db, complaint)

    mock_classify.assert_called_once_with(
        complaint.complaint_text
    )

    assert complaint.processing_route == "llm"
    assert complaint.category == "billing"
    assert complaint.subcategory == "charge_after_cancellation"
    assert complaint.priority == "high"
    assert complaint.status == "processed"
    assert complaint.workflow_dispatch_status == "dispatched"

    assert (
        complaint.customer_intent
        == "Resolve unexpected charge after cancellation"
    )

    assert (
        complaint.summary
        == "Customer was charged after cancelling their subscription."
    )

    mock_trigger_workflow.assert_called_once_with(
        complaint_id="CMP-TEST002",
        category="billing",
        subcategory="charge_after_cancellation",
        priority="high",
        processing_route="llm",
    )

@patch("app.services.processing_service.trigger_complaint_workflow")
@patch("app.services.processing_service.classify_complaint")
def test_llm_failure_marks_complaint_failed_and_does_not_trigger_workflow(
    mock_classify,
    mock_trigger_workflow,
):
    db = Mock()

    mock_classify.side_effect = RuntimeError(
        "Bedrock classification failed"
    )

    complaint = ComplaintDB(
        complaint_id="CMP-TEST003",
        customer_id="CUST-TEST003",
        channel="online",
        complaint_text=(
            "I cancelled last week but you have taken money "
            "from me again today."
        ),
        status="received",
    )

    with pytest.raises(
        RuntimeError,
        match="Bedrock classification failed",
    ):
        process_complaint(db, complaint)

    assert complaint.status == "failed"
    assert complaint.workflow_dispatch_status == "not_requested"

    mock_classify.assert_called_once_with(
        complaint.complaint_text
    )

    mock_trigger_workflow.assert_not_called()

    assert db.commit.call_count >= 2

@patch("app.services.processing_service.trigger_complaint_workflow")
@patch("app.services.processing_service.classify_complaint")
def test_insufficient_information_does_not_trigger_workflow(
    mock_classify,
    mock_trigger_workflow,
):
    db = Mock()

    mock_classify.return_value = ComplaintClassification(
        sufficient_information=False,
        category=ComplaintCategory.OTHER,
        subcategory=ComplaintSubcategory.OTHER,
        priority=ComplaintPriority.LOW,
        customer_intent="unclear",
        summary="Insufficient information to identify a specific complaint.",
    )

    complaint = ComplaintDB(
        complaint_id="CMP-TEST004",
        customer_id="CUST-TEST004",
        channel="online",
        complaint_text="nothing happened",
        status="received",
    )

    result = process_complaint(db, complaint)

    mock_classify.assert_called_once_with(
        complaint.complaint_text
    )

    mock_trigger_workflow.assert_not_called()

    assert result.status == "needs_information"
    assert result.workflow_dispatch_status == "not_requested"
    assert result.processing_route == "llm"
    assert result.category == "other"
    assert result.subcategory == "other"
    assert result.priority == "low"
    assert result.customer_intent == "unclear"


@patch("app.services.processing_service.trigger_complaint_workflow")
@patch("app.services.processing_service.classify_complaint")
def test_workflow_failure_preserves_successful_classification(
    mock_classify,
    mock_trigger_workflow,
):
    db = Mock()

    mock_classify.return_value = ComplaintClassification(
        sufficient_information=True,
        category=ComplaintCategory.BILLING,
        subcategory=ComplaintSubcategory.CHARGE_AFTER_CANCELLATION,
        priority=ComplaintPriority.HIGH,
        customer_intent="Investigate a post-cancellation charge",
        summary="Customer was charged after cancelling their subscription.",
    )
    mock_trigger_workflow.side_effect = RuntimeError("n8n unavailable")

    complaint = ComplaintDB(
        complaint_id="CMP-DISPATCH-FAIL",
        customer_id="CUST-DISPATCH-FAIL",
        channel="online",
        complaint_text="I cancelled, but you charged me again.",
        status="received",
    )

    result = process_complaint(db, complaint)

    assert result.status == "processed"
    assert result.workflow_dispatch_status == "failed"
    assert result.category == "billing"
    assert result.subcategory == "charge_after_cancellation"
    assert (
        result.summary
        == "Customer was charged after cancelling their subscription."
    )
    assert db.commit.call_count >= 3

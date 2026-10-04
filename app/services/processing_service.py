import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.complaint_db import ComplaintDB
from app.models.enums import ComplaintStatus, WorkflowDispatchStatus
from app.services.bedrock_service import classify_complaint
from app.services.n8n_service import trigger_complaint_workflow
from app.services.routing_service import route_complaint


logger = logging.getLogger(__name__)


def process_complaint(
    db: Session,
    complaint: ComplaintDB,
) -> ComplaintDB:

    complaint.status = ComplaintStatus.PROCESSING.value
    complaint.workflow_dispatch_status = (
        WorkflowDispatchStatus.NOT_REQUESTED.value
    )
    db.commit()

    try:
        decision = route_complaint(complaint.complaint_text)

        if decision.route.value == "deterministic":
            complaint.processing_route = "deterministic"
            complaint.category = (
                decision.category.value if decision.category else None
            )

            complaint.subcategory = (
                decision.subcategory.value
                if decision.subcategory
                else None
            )

            complaint.priority = (
                decision.priority.value if decision.priority else None
            )
            complaint.summary = decision.summary
            complaint.model_used = None

        else:
            classification = classify_complaint(
                complaint.complaint_text
            )

            if not classification.sufficient_information:
                complaint.processing_route = "llm"
                complaint.category = classification.category.value
                complaint.subcategory = classification.subcategory.value
                complaint.priority = classification.priority.value
                complaint.customer_intent = classification.customer_intent
                complaint.summary = classification.summary
                complaint.model_used = settings.bedrock_model_id
                complaint.status = ComplaintStatus.NEEDS_INFORMATION.value

                db.commit()
                db.refresh(complaint)

                return complaint

            complaint.processing_route = "llm"
            complaint.category = classification.category.value
            complaint.subcategory = classification.subcategory.value
            complaint.priority = classification.priority.value
            complaint.customer_intent = classification.customer_intent
            complaint.summary = classification.summary
            complaint.model_used = settings.bedrock_model_id


        complaint.status = ComplaintStatus.PROCESSED.value
        complaint.workflow_dispatch_status = (
            WorkflowDispatchStatus.PENDING.value
        )
        db.commit()
        db.refresh(complaint)

    except Exception:
        complaint.status = ComplaintStatus.FAILED.value
        complaint.workflow_dispatch_status = (
            WorkflowDispatchStatus.NOT_REQUESTED.value
        )
        db.commit()
        raise

    try:
        trigger_complaint_workflow(
            complaint_id=complaint.complaint_id,
            category=complaint.category,
            subcategory=complaint.subcategory,
            priority=complaint.priority,
            processing_route=complaint.processing_route,
        )
    except Exception:
        complaint.workflow_dispatch_status = (
            WorkflowDispatchStatus.FAILED.value
        )
        db.commit()
        db.refresh(complaint)
        logger.exception(
            "Workflow dispatch failed for complaint %s",
            complaint.complaint_id,
        )
        return complaint

    complaint.workflow_dispatch_status = (
        WorkflowDispatchStatus.DISPATCHED.value
    )
    db.commit()
    db.refresh(complaint)
    return complaint

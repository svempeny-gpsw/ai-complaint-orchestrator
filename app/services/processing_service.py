from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.complaint_db import ComplaintDB
from app.services.bedrock_service import classify_complaint
from app.services.n8n_service import trigger_complaint_workflow
from app.services.routing_service import route_complaint


def process_complaint(
    db: Session,
    complaint: ComplaintDB,
) -> ComplaintDB:

    complaint.status = "processing"
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
            complaint.summary = decision.reason
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
                complaint.status = "needs_information"

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


        complaint.status = "resolved"
        db.commit()
        db.refresh(complaint)

        trigger_complaint_workflow(
            complaint_id=complaint.complaint_id,
            category=complaint.category,
            subcategory=complaint.subcategory,
            priority=complaint.priority,
            processing_route=complaint.processing_route,
        )

        return complaint

    except Exception:
        complaint.status = "failed"
        db.commit()
        raise

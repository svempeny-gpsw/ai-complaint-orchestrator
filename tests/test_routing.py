from app.models.complaint import (
    ComplaintCategory,
    ProcessingRoute,
)

from app.models.classification import ComplaintSubcategory
from app.models.complaint import ComplaintCategory, ProcessingRoute
from app.services.routing_service import route_complaint


def test_duplicate_charge_is_deterministic():
    result = route_complaint(
        "I have a duplicate charge on my account."
    )

    assert result.route == ProcessingRoute.DETERMINISTIC
    assert result.category == ComplaintCategory.BILLING
    assert result.subcategory == ComplaintSubcategory.DUPLICATE_CHARGE


def test_ambiguous_complaint_uses_llm():
    result = route_complaint(
        "I cancelled last week but you have taken money from me again."
    )

    assert result.route == ProcessingRoute.LLM
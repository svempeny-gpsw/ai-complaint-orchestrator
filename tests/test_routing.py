import pytest

from app.models.enums import (
    ComplaintCategory,
    ComplaintSubcategory,
    ProcessingRoute,
)
from app.services.routing_service import route_complaint


def test_duplicate_charge_is_deterministic():
    result = route_complaint(
        "I have a duplicate charge on my account."
    )

    assert result.route == ProcessingRoute.DETERMINISTIC
    assert result.category == ComplaintCategory.BILLING
    assert result.subcategory == ComplaintSubcategory.DUPLICATE_CHARGE
    assert result.summary == "Customer reports a duplicate charge."
    assert result.reason == "Explicit duplicate-charge phrase detected"


def test_ambiguous_complaint_uses_llm():
    result = route_complaint(
        "I cancelled last week but you have taken money from me again."
    )

    assert result.route == ProcessingRoute.LLM


@pytest.mark.parametrize(
    "complaint_text",
    [
        "I do not have a duplicate charge, but my invoice is confusing.",
        "There's no duplicate charge — I just want a receipt.",
        (
            "A friend mentioned a duplicate charge; "
            "I don't think it applies to me."
        ),
    ],
)
def test_negated_or_disclaimed_duplicate_charge_uses_llm(complaint_text):
    result = route_complaint(complaint_text)

    assert result.route == ProcessingRoute.LLM
    assert result.subcategory is None

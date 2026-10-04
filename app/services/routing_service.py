from dataclasses import dataclass

from app.models.enums import (
    ComplaintCategory,
    ComplaintPriority,
    ComplaintSubcategory,
    ProcessingRoute,
)


DUPLICATE_CHARGE_NEGATIONS = (
    "no duplicate charge",
    "not a duplicate charge",
    "not have a duplicate charge",
    "without a duplicate charge",
)

DUPLICATE_CHARGE_DISCLAIMERS = (
    "does not apply to me",
    "doesn't apply to me",
    "do not think it applies to me",
    "don't think it applies to me",
)


@dataclass
class RoutingDecision:
    route: ProcessingRoute
    category: ComplaintCategory | None = None
    subcategory: ComplaintSubcategory | None = None
    priority: ComplaintPriority | None = None
    summary: str | None = None
    reason: str | None = None


def route_complaint(text: str) -> RoutingDecision:
    normalized = " ".join(text.lower().split())

    # Highly explicit billing case
    has_duplicate_charge = "duplicate charge" in normalized
    has_negation = any(
        phrase in normalized for phrase in DUPLICATE_CHARGE_NEGATIONS
    )
    has_disclaimer = any(
        phrase in normalized for phrase in DUPLICATE_CHARGE_DISCLAIMERS
    )

    if has_duplicate_charge and not (has_negation or has_disclaimer):
        return RoutingDecision(
            route=ProcessingRoute.DETERMINISTIC,
            category=ComplaintCategory.BILLING,
            subcategory=ComplaintSubcategory.DUPLICATE_CHARGE,
            priority=ComplaintPriority.HIGH,
            summary="Customer reports a duplicate charge.",
            reason="Explicit duplicate-charge phrase detected",
        )

    # Highly explicit delivery case
    if "order not delivered" in normalized:
        return RoutingDecision(
            route=ProcessingRoute.DETERMINISTIC,
            category=ComplaintCategory.DELIVERY,
            subcategory=ComplaintSubcategory.MISSING_DELIVERY,
            priority=ComplaintPriority.MEDIUM,
            summary="Customer reports that an order was not delivered.",
            reason="Explicit delivery failure phrase detected",
        )

    # Everything ambiguous/unstructured goes to Claude
    return RoutingDecision(
        route=ProcessingRoute.LLM,
        reason="Complaint requires semantic classification",
    )

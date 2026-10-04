from dataclasses import dataclass

from app.models.enums import (
    ComplaintCategory,
    ComplaintPriority,
    ComplaintSubcategory,
    ProcessingRoute,
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
    normalized = text.lower()

    # Highly explicit billing case
    if "duplicate charge" in normalized:
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

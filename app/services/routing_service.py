from dataclasses import dataclass
from app.models.classification import ComplaintSubcategory

from app.models.complaint import (
    ComplaintCategory,
    ComplaintPriority,
    ProcessingRoute,
)


@dataclass
class RoutingDecision:
    route: ProcessingRoute
    category: ComplaintCategory | None = None
    subcategory: ComplaintSubcategory | None = None
    priority: ComplaintPriority | None = None
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
            reason="Explicit duplicate-charge phrase detected",
        )

    # Highly explicit delivery case
    if "order not delivered" in normalized:
        return RoutingDecision(
            route=ProcessingRoute.DETERMINISTIC,
            category=ComplaintCategory.DELIVERY,
            subcategory=ComplaintSubcategory.MISSING_DELIVERY,
            priority=ComplaintPriority.MEDIUM,
            reason="Explicit delivery failure phrase detected",
        )

    # Everything ambiguous/unstructured goes to Claude
    return RoutingDecision(
        route=ProcessingRoute.LLM,
        reason="Complaint requires semantic classification",
    )
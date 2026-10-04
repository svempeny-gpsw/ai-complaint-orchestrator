from dataclasses import dataclass

from app.models.complaint_db import ComplaintDB
from app.models.enums import (
    ComplaintCategory,
    ComplaintStatus,
    ComplaintSubcategory,
)


@dataclass(frozen=True)
class PermittedComplaintAction:
    action: str
    action_status: str
    reason: str


ACTION_POLICIES = {
    (
        ComplaintCategory.BILLING.value,
        ComplaintSubcategory.DUPLICATE_CHARGE.value,
    ): PermittedComplaintAction(
        action="initiate_duplicate_charge_refund",
        action_status="initiated",
        reason=(
            "Duplicate charge classification initiated refund "
            "eligibility review"
        ),
    ),
    (
        ComplaintCategory.BILLING.value,
        ComplaintSubcategory.CHARGE_AFTER_CANCELLATION.value,
    ): PermittedComplaintAction(
        action="investigate_post_cancellation_charge",
        action_status="initiated",
        reason=(
            "Post-cancellation charge requires deterministic "
            "billing investigation"
        ),
    ),
}


def determine_permitted_action(
    complaint: ComplaintDB,
) -> PermittedComplaintAction | None:
    if complaint.status != ComplaintStatus.PROCESSED.value:
        return None

    return ACTION_POLICIES.get(
        (complaint.category, complaint.subcategory)
    )

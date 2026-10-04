from pydantic import BaseModel, Field

from app.models.enums import (
    ComplaintCategory,
    ComplaintPriority,
    ComplaintSubcategory,
)


class ComplaintClassification(BaseModel):
    sufficient_information: bool = Field(
        description=(
            "True only when the complaint contains enough information "
            "to identify a meaningful customer issue"
        )
    )

    category: ComplaintCategory
    subcategory: ComplaintSubcategory
    priority: ComplaintPriority

    customer_intent: str = Field(
        description="What outcome the customer appears to be seeking"
    )

    summary: str = Field(
        description="Short factual summary of the complaint"
    )

from pydantic import BaseModel, Field


class PhoneComplaintCreate(BaseModel):
    customer_id: str = Field(min_length=1)

    transcript: str = Field(
        min_length=10,
        description="Speech-to-text transcript of the customer's phone complaint",
    )
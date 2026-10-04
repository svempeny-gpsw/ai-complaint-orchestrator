import json
from functools import lru_cache

import boto3
from botocore.config import Config

from app.core.config import settings
from app.models.classification import ComplaintClassification


SYSTEM_PROMPT = """
You classify customer complaints.

Return only valid JSON matching this structure:

{
  "sufficient_information": true,
  "category": "billing | delivery | account | product | service | other",
  "subcategory": "duplicate_charge | charge_after_cancellation | refund_not_received | delivery_delay | missing_delivery | account_access | product_issue | service_issue | other",
  "priority": "low | medium | high",
  "customer_intent": "short description",
  "summary": "short factual summary"
}

Rules:
- Do not include markdown.
- Do not include explanations outside the JSON.
- Do not invent facts not present in the complaint.
- Do not approve refunds or other business actions.
- Set sufficient_information to false when the input does not contain
  enough information to identify a meaningful customer complaint.
- When sufficient_information is false:
  - category must be "other"
  - subcategory must be "other"
  - priority must be "low"
  - customer_intent must be "unclear"
  - summary must explain that there is insufficient information.
"""


BEDROCK_CLIENT_CONFIG = Config(
    retries={"total_max_attempts": 3, "mode": "standard"},
    connect_timeout=5,
    read_timeout=30,
)


@lru_cache(maxsize=1)
def _create_bedrock_client():
    session = boto3.Session(
        profile_name=settings.aws_profile,
        region_name=settings.aws_region,
    )

    return session.client(
        "bedrock-runtime",
        config=BEDROCK_CLIENT_CONFIG,
    )


def classify_complaint(
    complaint_text: str,
) -> ComplaintClassification:

    bedrock = _create_bedrock_client()

    response = bedrock.converse(
        modelId=settings.bedrock_model_id,
        system=[
            {
                "text": SYSTEM_PROMPT,
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": complaint_text,
                    }
                ],
            }
        ],
        inferenceConfig={
            "maxTokens": 500,
            "temperature": 0,
        },
    )

    output_text = response["output"]["message"]["content"][0]["text"]

    data = json.loads(output_text)

    return ComplaintClassification.model_validate(data)

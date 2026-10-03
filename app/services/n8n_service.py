import httpx

from app.core.config import settings


def trigger_complaint_workflow(
    complaint_id: str,
    category: str,
    subcategory: str | None,
    priority: str,
    processing_route: str,
) -> None:
    payload = {
        "complaint_id": complaint_id,
        "category": category,
        "subcategory": subcategory,
        "priority": priority,
        "processing_route": processing_route,
    }

    response = httpx.post(
        settings.n8n_webhook_url,
        json=payload,
        timeout=10.0,
    )

    response.raise_for_status()
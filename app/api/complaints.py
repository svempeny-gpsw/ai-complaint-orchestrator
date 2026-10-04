from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.phone_complaint import PhoneComplaintCreate
from app.core.database import get_db
from app.models.complaint import ComplaintCreate, ComplaintResponse
from app.services.complaint_service import (
    create_complaint,
    get_complaint,
)

from app.models.complaint_action import (
    ComplaintActionRequest,
    ComplaintActionResponse,
)

from app.services.complaint_action_service import (
    ComplaintActionNotPermittedError,
    ComplaintNotFoundError,
    create_complaint_action,
    get_complaint_actions,
)

router = APIRouter(
    prefix="/complaints",
    tags=["complaints"],
)


@router.post(
    "",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_complaint(
    complaint: ComplaintCreate,
    db: Session = Depends(get_db),
) -> ComplaintResponse:

    return create_complaint(db, complaint)


@router.post(
    "/phone",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_phone_complaint(
    phone_complaint: PhoneComplaintCreate,
    db: Session = Depends(get_db),
):
    complaint = ComplaintCreate(
        customer_id=phone_complaint.customer_id,
        channel="phone",
        complaint_text=phone_complaint.transcript,
    )

    return create_complaint(
        db=db,
        complaint=complaint,
    )


@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse,
)
def read_complaint(
    complaint_id: str,
    db: Session = Depends(get_db),
) -> ComplaintResponse:

    complaint = get_complaint(db, complaint_id)

    if complaint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found",
        )

    return complaint

@router.post(
    "/{complaint_id}/actions",
    response_model=ComplaintActionResponse,
    status_code=status.HTTP_200_OK,
)
def add_complaint_action(
    complaint_id: str,
    _request: ComplaintActionRequest | None = None,
    db: Session = Depends(get_db),
) -> ComplaintActionResponse:

    try:
        return create_complaint_action(
            db=db,
            complaint_id=complaint_id,
        )
    except ComplaintNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ComplaintActionNotPermittedError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.get(
    "/{complaint_id}/actions",
    response_model=list[ComplaintActionResponse],
)
def read_complaint_actions(
    complaint_id: str,
    db: Session = Depends(get_db),
) -> list[ComplaintActionResponse]:

    complaint = get_complaint(db, complaint_id)

    if complaint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found",
        )

    return get_complaint_actions(
        db=db,
        complaint_id=complaint_id,
    )

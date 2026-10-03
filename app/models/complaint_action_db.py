from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ComplaintActionDB(Base):
    __tablename__ = "complaint_actions"
    __table_args__ = (
        UniqueConstraint(
            "complaint_id",
            "action",
            name="uq_complaint_action",
        ),
    )

    action_id: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
    )

    complaint_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("complaints.complaint_id"),
        nullable=False,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    action_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ComplaintDB(Base):
    __tablename__ = "complaints"

    complaint_id: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
    )

    customer_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    channel: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    complaint_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="received",
    )

    # Processing result
    processing_route: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    category: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    subcategory: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    priority: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    customer_intent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    model_used: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
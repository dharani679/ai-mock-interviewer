from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.db.database import Base

if TYPE_CHECKING:
    from apps.models.answer import Answer
    from apps.models.analytics import Analytics
    from apps.models.feedback import Feedback
    from apps.models.question import Question
    from apps.models.user import User


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[str] = mapped_column(String(150), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(100))
    mode: Mapped[str | None] = mapped_column(String(80))
    difficulty: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30), default="created", nullable=False)
    job_description: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship(back_populates="interviews")
    questions: Mapped[list["Question"]] = relationship(
        back_populates="interview",
        cascade="all, delete-orphan",
    )
    answers: Mapped[list["Answer"]] = relationship(
        back_populates="interview",
        cascade="all, delete-orphan",
    )
    feedback: Mapped[list["Feedback"]] = relationship(
        back_populates="interview",
        cascade="all, delete-orphan",
    )
    analytics: Mapped[list["Analytics"]] = relationship(
        back_populates="interview",
        cascade="all, delete-orphan",
    )

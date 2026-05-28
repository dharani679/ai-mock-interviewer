from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.db.database import Base

if TYPE_CHECKING:
    from apps.models.resume import Resume
    from apps.models.user import User


class EmbeddingMetadata(Base):
    __tablename__ = "embeddings_metadata"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    resume_id: Mapped[int | None] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    collection_name: Mapped[str] = mapped_column(String(150), nullable=False)
    document_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="embeddings_metadata")
    resume: Mapped["Resume | None"] = relationship(back_populates="embeddings_metadata")

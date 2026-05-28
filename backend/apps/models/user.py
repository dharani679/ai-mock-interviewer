from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.db.database import Base

if TYPE_CHECKING:
    from apps.models.analytics import Analytics
    from apps.models.embedding_metadata import EmbeddingMetadata
    from apps.models.interview import Interview
    from apps.models.resume import Resume


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    interviews: Mapped[list["Interview"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    resumes: Mapped[list["Resume"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    analytics: Mapped[list["Analytics"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    embeddings_metadata: Mapped[list["EmbeddingMetadata"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

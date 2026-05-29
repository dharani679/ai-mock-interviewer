from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.db.database import Base

if TYPE_CHECKING:
    from apps.models.embedding_metadata import EmbeddingMetadata


class Embedding(Base):
    __tablename__ = "embeddings"
    __table_args__ = (Index("ix_embeddings_metadata_fk_id", "metadata_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    metadata_id: Mapped[int] = mapped_column(
        ForeignKey("embeddings_metadata.id", ondelete="CASCADE"),
    )
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    vector_json: Mapped[list[float]] = mapped_column(JSON, nullable=False)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    metadata_ref: Mapped["EmbeddingMetadata"] = relationship(back_populates="embeddings")

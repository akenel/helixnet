# File: src/db/models/camper_document_model.py
"""
CamperDocumentModel - Document/file storage tracking for Camper & Tour.
Files stored in MinIO, metadata tracked here. Linked to any entity type.

"Keep your eyes and ears open."
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CamperDocumentModel(Base):
    """
    Tracks documents uploaded to MinIO for any Camper & Tour entity.
    Photos, PDFs, quotation documents, invoices, etc.
    """
    __tablename__ = 'camper_documents'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Polymorphic link to any entity
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="job, customer, vehicle, quotation, invoice, po"
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )

    # File metadata
    file_name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    file_type: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="MIME type"
    )
    file_size: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Size in bytes"
    )
    minio_object_key: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="Path in MinIO bucket"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # Audit
    uploaded_by: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self):
        return f"<CamperDocument(name='{self.file_name}', entity={self.entity_type}/{self.entity_id})>"

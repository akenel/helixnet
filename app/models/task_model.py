import datetime
import uuid
from sqlalchemy import Column, String, DateTime, func, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.db.database import Base

class TaskResult(Base):
    """
    Model to store persistent results and metadata for asynchronous tasks.
    This goes beyond the short-lived Celery state in Redis/RabbitMQ.
    """
    __tablename__ = "task_results"
    
    __mapper_args__ = {
        'polymorphic_identity': 'task_result',
        'polymorphic_on': 'type'
    }

    # Primary Key using UUID
    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # Celery Task ID (tracked separately)
    celery_task_id = Column(String(64), unique=True, nullable=False)

    # Type discriminator for polymorphic identity
    type = Column(String(50), nullable=False)

    # Status: PENDING, STARTED, SUCCESS, FAILURE
    status = Column(String, index=True, default="PENDING", nullable=False)

    # Detailed result or error message (Stored as JSON/dict in Python)
    result_data = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<TaskResult(id='{self.id}', status='{self.status}')>"

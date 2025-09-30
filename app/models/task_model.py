import datetime
from sqlalchemy import Column, String, DateTime, func, JSON
from app.db.database import Base # <<< UPDATED IMPORT PATH

class TaskResult(Base):
    """
    Model to store persistent results and metadata for asynchronous tasks.
    This goes beyond the short-lived Celery state in Redis/RabbitMQ.
    """
    __tablename__ = "task_results"

    # Primary Key
    id = Column(
        String, 
        primary_key=True, 
        index=True, 
        # Using a UUID or unique task ID from Celery is better than an auto-increment integer here.
        # We will use the Celery Task ID as the primary key.
    ) 

    # Celery Task ID (used as primary key here, but often tracked separately)
    celery_task_id = Column(String, unique=True, nullable=False)

    # Status: PENDING, STARTED, SUCCESS, FAILURE
    status = Column(String, index=True, default="PENDING", nullable=False)

    # Detailed result or error message (Stored as JSON/dict in Python)
    result_data = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<TaskResult(id='{self.id}', status='{self.status}')>"

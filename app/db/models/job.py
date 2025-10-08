import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, UUID
from sqlalchemy.orm import relationship
# SQLAlchemy Job Model
# Assuming Base is defined in app/db/database.py
from app.db.database import Base 
# Assuming you have a User model you can link to
# from app.db.models.user import UserModel 
# app/db/models/job.py: 
# The actual SQLAlchemy model definition for the jobs table in Postgres.
# Import the JobStatus Enum we just defined
from app.schemas.job import JobStatus 

# Helper for UTC time creation
def now_utc():
    return datetime.now(timezone.utc)

class JobModel(Base):
    """
    SQLAlchemy model for the 'jobs' table. Tracks asynchronous job submissions.
    """
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign Key linking the job to the user who submitted it
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True) 
    
    # Link to the Celery Task ID for status checking
    celery_task_id = Column(String, index=True, nullable=True) 

    # Core data fields (from JobBase schema)
    input_file_path = Column(String, nullable=False)
    template_name = Column(String, nullable=False)

    # Job Status using the Enum
    status = Column(Enum(JobStatus, name="job_status_enum", create_type=True), 
                    default=JobStatus.PENDING, 
                    nullable=False, 
                    index=True)
    
    # Final result path (MinIO URL)
    output_url = Column(String, nullable=True)

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    # Relationship back to the User model (assuming it's named 'users')
    # user = relationship("UserModel", back_populates="jobs") 
    
    def __repr__(self):
        return f"<Job(id='{self.id}', status='{self.status}', template='{self.template_name}')>"

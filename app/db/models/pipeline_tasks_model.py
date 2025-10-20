import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.models.base import Base # Assuming Base is imported from your shared structure
from app.db.models.artifact import Artifact # Import Artifact for the relationship

class PipelineTask(Base):
    """
    Represents a specific step (task) executed on an Artifact within a pipeline. 
    This is used for granular history, retry tracking, and state management.
    """
    __tablename__ = "pipeline_tasks"

    # --- IDENTIFICATION ---
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign key link to the Artifact being processed
    artifact_id = Column(UUID(as_uuid=True), ForeignKey('artifacts.id'), nullable=False, index=True)
    
    # Relationship back to the Artifact model
    artifact = relationship("Artifact", backref="tasks")

    # The name of the specific task (e.g., 'Validate_Payload', 'Transform_to_ABAP', 'Send_to_SAP')
    task_name = Column(String(128), nullable=False) 

    # --- EXECUTION STATE ---
    
    # Status of this specific task execution (e.g., PENDING, SUCCESS, FAILED)
    status = Column(String(50), nullable=False, default="PENDING", index=True) 

    # Sequential order of this task within the pipeline definition
    execution_order = Column(Integer, nullable=False) 
    
    # Number of times this specific task has been attempted for this artifact
    retry_count = Column(Integer, default=0, nullable=False)
    
    # LLM-generated error description or standard traceback on failure
    error_message = Column(Text, nullable=True) 

    # --- TIMESTAMPS ---
    
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    
    # --- AUDIT ---
    
    # A complete log of all attempts, including timestamps and brief error summaries
    history = Column(JSON, nullable=False, default=lambda: []) 

    def __repr__(self):
        return f"<PipelineTask id={self.id} artifact_id={self.artifact_id} task='{self.task_name}' status='{self.status}'>"

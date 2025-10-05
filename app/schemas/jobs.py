# app/schemas/jobs.py
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from typing import Dict, Any, Optional

class JobSubmission(BaseModel):
    # This is the expected input payload from the user
    input_data: Dict[str, Any]

class JobStatus(BaseModel):
    # CRITICAL: Map the DB ORM object's 'id' attribute to the Pydantic field 'job_id'
    job_id: UUID = Field(alias='id') 
    status: str
    message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    
    # CRITICAL: This configuration tells Pydantic to read data directly 
    # from the SQLAlchemy ORM object's attributes (columns).
    model_config = ConfigDict(
        from_attributes=True, 
        populate_by_name=True # Allows Pydantic to match the 'job_id' field name OR the 'id' alias
    )
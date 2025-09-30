# app/schemas/tasks.py
"""
Pydantic Schemas for Celery Task input and monitoring.
"""
from pydantic import BaseModel
from uuid import UUID
from typing import Dict, Any

class JobSubmission(BaseModel):
    """
    Schema for input when submitting a new background job.
    Requires a user ID to link the job result and generic input data.
    """
    user_id: UUID
    input_data: Dict[str, Any]
    
    class Config:
        """Example usage: JobSubmission(user_id='...', input_data={'parameter1': 10})"""
        json_schema_extra = {
            "example": {
                "user_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "input_data": {
                    "report_name": "Monthly_Analysis",
                    "priority": "high"
                }
            }
        }

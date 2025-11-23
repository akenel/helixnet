"""
API Router for managing background jobs (Jobs and related Tasks).
This version eliminates all SHIM warnings and prepares for integration with the real JobService layer.
"""
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Any
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    File,
    UploadFile,
)
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, ConfigDict

from src.core.local_auth_service import get_current_user
from src.db.database import get_db_session
from src.db.models.user_model import UserModel
from src.schemas.job_schema import JobSubmission

logger = logging.getLogger(__name__)

jobs_router = APIRouter(prefix="/jobs", tags=["Jobs"])

# ============================================================================
# 🧠 Models (Updated for Pydantic v2)
# ============================================================================

class JobRead(BaseModel):
    """Represents a job record returned to the user."""
    id: UUID
    title: str
    status: str
    owner_email: str

    model_config = ConfigDict(from_attributes=True)


class JobCreate(BaseModel):
    """Represents data required to create a new job."""
    title: str
    payload: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Triple Roundhouse Compliance Report",
                    "payload": {
                        "report_type": "quarterly_audit",
                        "target_user_ids": [
                            "9a326614-478f-4332-b65d-8824709cfa1e",
                            "b3f0c2e1-a7d9-4b8c-8c1d-6b0d9e5f4a7b"
                        ],
                        "complexity_level": 9000,
                        "priority": "HIGH"
                    },
                }
            ]
        }
    )


class JobFileResponse(BaseModel):
    """The enriched response model for file uploads."""
    job_id: UUID
    status: str
    uploaded_files: Dict[str, str]

# ============================================================================
# ⚙️ TEMPORARY IN-MEMORY JOB STORE (until JobService is live)
# ============================================================================
IN_MEMORY_JOBS: Dict[str, List[Dict[str, Any]]] = {}

def _user_key(user: UserModel) -> str:
    return str(user.id)

async def _save_job(job_data: Dict[str, Any], current_user: UserModel) -> Dict[str, Any]:
    """Temporary function to save a job in memory."""
    user_key = _user_key(current_user)
    job_data["id"] = uuid.uuid4()
    job_data["owner_email"] = current_user.email
    job_data["status"] = job_data.get("status", "PENDING")

    IN_MEMORY_JOBS.setdefault(user_key, []).append(job_data)
    return job_data

async def _list_jobs(current_user: UserModel) -> List[Dict[str, Any]]:
    return IN_MEMORY_JOBS.get(_user_key(current_user), [])

async def _get_job(job_id: UUID, current_user: UserModel) -> Dict[str, Any] | None:
    jobs = await _list_jobs(current_user)
    return next((j for j in jobs if j["id"] == job_id), None)

async def _delete_job(job_id: UUID, current_user: UserModel) -> None:
    user_key = _user_key(current_user)
    if user_key not in IN_MEMORY_JOBS:
        raise ValueError(f"Job ID {job_id} not found.")

    before = len(IN_MEMORY_JOBS[user_key])
    IN_MEMORY_JOBS[user_key] = [j for j in IN_MEMORY_JOBS[user_key] if j["id"] != job_id]

    if len(IN_MEMORY_JOBS[user_key]) == before:
        raise ValueError(f"Job ID {job_id} not found.")

# ============================================================================
# 🚀 ROUTES
# ============================================================================

@jobs_router.get("", response_model=List[JobRead])
async def list_jobs(
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user),
):
    """List all jobs owned by the current authenticated user."""
    jobs_data = await _list_jobs(current_user)
    logger.info(f"User {current_user.email} retrieved {len(jobs_data)} job(s).")
    return [JobRead.model_validate(job) for job in jobs_data]


@jobs_router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user),
):
    """Retrieve a single job by ID."""
    job_data = await _get_job(job_id, current_user)
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found or unauthorized.")
    return JobRead.model_validate(job_data)


@jobs_router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job_no_files(
    job_in: JobCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user),
):
    """Create a new background job."""
    job = await _save_job(job_in.model_dump(), current_user)
    logger.info(f"Created job {job['id']} for user {current_user.email}")
    return JobRead.model_validate(job)


@jobs_router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user),
):
    """Delete a job by ID."""
    try:
        await _delete_job(job_id, current_user)
        logger.info(f"Deleted job {job_id} for user {current_user.email}")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@jobs_router.post("/upload", response_model=JobFileResponse, status_code=status.HTTP_201_CREATED)
async def create_job_with_files(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    content_file: UploadFile = File(...),
    context_file: UploadFile = File(...),
    template_file: UploadFile = File(...),
    schema_file: UploadFile = File(...),
):
    """Create a new job via multiple file uploads."""
    upload_dir = Path("/data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "content": content_file,
        "context": context_file,
        "template": template_file,
        "schema": schema_file,
    }

    uploaded_paths = {}
    for key, file in files.items():
        file_path = upload_dir / f"{uuid.uuid4()}_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())
        uploaded_paths[key] = str(file_path)

    job_submission = JobSubmission(
        task_name="process_job",
        input_data=uploaded_paths,
    )
    job_data = {
        "title": f"File Job: {content_file.filename}",
        "payload": job_submission.model_dump(),
    }
    saved_job = await _save_job(job_data, current_user)
    logger.info(f"Job {saved_job['id']} created from file upload.")

    return JobFileResponse(
        job_id=saved_job["id"],
        status=saved_job["status"],
        uploaded_files={k: v.filename for k, v in files.items()},
    )

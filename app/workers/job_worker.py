from celery import shared_task
from datetime import datetime, UTC
from sqlalchemy.orm import Session
import json, yaml, logging
from jinja2 import Template
import requests
from app.db.session import SyncSessionLocal   # a synchronous session factory
from app.db.models.job_model import Job, JobStatus
from app.services.job_service import update_job_status_for_celery

logger = logging.getLogger(__name__)

@shared_task(name="process_job")
def process_job(job_id: str):
    """Main async worker that processes one job."""
    db: Session = SyncSessionLocal()
    try:
        job: Job = db.get(Job, job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        update_job_status_for_celery(db, job.job_id, {"status": "PROCESSING"})
        logger.info(f"Processing job {job.job_id} for user {job.user_id}")

        # --- pull file paths from job.input_data ---
        data = job.input_data
        content_path = data.get("content_path")
        context_path = data.get("context_path")
        template_path = data.get("template_path")
        schema_path = data.get("schema_path")

        # For prototype, assume local filesystem
        with open(content_path) as f:
            content = f.read()
        with open(context_path) as f:
            context = yaml.safe_load(f)
        with open(template_path) as f:
            template_str = f.read()
        with open(schema_path) as f:
            schema = json.load(f)

        # --- render prompt ---
        prompt = Template(template_str).render(content=content, context=context)

        # --- call local LLM (Ollama) ---
        response = requests.post(
            "http://ollama:11434/api/generate",
            json={"model": "llama2", "prompt": prompt},
            timeout=120,
        )
        result_text = response.text

        # --- save output ---
        output_path = f"/data/results/{job.job_id}.json"
        with open(output_path, "w") as f:
            f.write(result_text)

        update_job_status_for_celery(
            db,
            job.job_id,
            {"status": "COMPLETED", "finished_at": datetime.now(UTC)},
        )
        logger.info(f"✅ Job {job.job_id} completed.")
    except Exception as e:
        logger.exception(e)
        update_job_status_for_celery(
            db,
            job_id,
            {"status": "FAILED", "error_log": str(e)},
        )
    finally:
        db.close()

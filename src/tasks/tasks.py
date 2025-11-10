import logging
from src.tasks.celery_app import celery_app # Assuming celery app is defined here

logger = logging.getLogger(__name__)

@celery_app.task(acks_late=True, name="src.tasks.tasks.run_heavy_computation")
def run_heavy_computation(job_id: str) -> dict:
    """
    A placeholder task to verify the Celery worker is running and connected.
    
    This function simulates a heavy computational task. We use an explicit 
    'name' argument in the decorator to ensure it registers correctly in 
    the Celery worker process.
    """
    logger.info(f"Starting heavy computation for Job ID: {job_id}")
    
    # Simulate work being done
    import time
    time.sleep(1) 
    
    logger.info(f"Finished computation for Job ID: {job_id}")
    
    # Return a dummy result structure
    return {
        "job_id": job_id,
        "status": "SUCCESS",
        "result_data": "Simulation Complete"
    }

@celery_app.task(acks_late=True, name="src.tasks.tasks.check_health")
def check_health() -> str:
    """A simple task used by the health check endpoint to verify task execution."""
    return "Celery worker is operational."

@celery_app.task(name="src.tasks.tasks.say_hello")
def say_hello():
    """Scheduled task to log a hello message."""
    logger.info("👋 Hello from Celery Beat!")
    return "Hello logged."

@celery_app.task(name="src.tasks.tasks.system_healthcheck")
def system_healthcheck():
    """Scheduled task to run periodic system checks."""
    logger.info("🩺 Running periodic system health check...")
    # In a real app, this would check DB connections, third-party services, etc.
    return "System health check complete."

logger.info("Task module 'src.tasks.tasks' imported successfully.")

# app/routes/tasks.py
from fastapi import APIRouter
from app.tasks.tasks import say_hello, system_healthcheck, process_job

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/hello")
def trigger_hello():
    result = say_hello.delay()
    return {"task_id": result.id, "status": "queued"}

@router.get("/healthcheck")
def trigger_healthcheck():
    result = system_healthcheck.delay()
    return {"task_id": result.id, "status": "queued"}

@router.post("/process")
def trigger_process(data: dict):
    result = process_job.delay(data)
    return {"task_id": result.id, "status": "queued"}

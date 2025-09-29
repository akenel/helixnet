# app/main.py
from fastapi import FastAPI
from app.routes.tasks import router as tasks_router  # ✅ correct router import
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | 🚀 HelixNet | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(title="HelixNet 🚀")

# Attach the Celery-task router (REST endpoints)
app.include_router(tasks_router)

@app.get("/health")
def health():
    return {"status": "ok", "msg": "HelixNet is running RR ✅"}

# src/tasks/celery.py

from venv import logger
from celery import Celery

app = Celery(
    'tasks',
    broker='amqp://helix_user:helix_pass@rabbitmq:5672//'
)
# In your Celery configuration settings

app.conf.beat_schedule = {
    # Unique identifier for the schedule entry
    'heartbeat-check-30-seconds': {
        'task': 'src.tasks.celery_app.echo_beat_heartbeat', 
        'schedule': 60.0,
        'args': ('Scheduled by Celery Beat!',)
    },
    # ... any other periodic tasks ...

    'double-check-30-seconds': {
        'task': 'src.tasks.celery_app.example_task', 
        'schedule': 30.0,
        'args': ('🏗️ 🌼 🚢 🥬 💦 Example Scheduled by Celery Beat! 🧩',)
    },


}

# Optional: Ensure the timezone is set for consistent scheduling
app.conf.timezone = 'UTC' # Or your local timezone like 'Europe/Zurich'
# Define your tasks here
@app.task
def example_task(message="💦 Example Task ran with Message: 🏗️ Celery Beat is alive and scheduling."):
    logger.info(f"💦 Example Task: {message} 🏗️  ◾ 🚢 ◾ 💦")
    print(f"Example task ran without any 🏗️ Issues as Example Logic 🚢 FYI message: {message}")
    return message

@app.task
def echo_beat_heartbeat(message="Celery Beat is alive and scheduling."):
    """
    A simple task to be run periodically by Celery Beat to confirm it's working.
    """
    logger.info(f"❤️ HEARTBEAT: {message} 🏗️  ◾ 🚢 ◾ 💦")
    # Note: This task still requires a Celery Worker to execute it.
    return message

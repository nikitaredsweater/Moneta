from celery import Celery
import os

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "pdf_tasks",
    broker=CELERY_BROKER_URL,
    backend=None,  # Optional: add Redis backend if you want task results
    include=[
        "app.workers.tasks",        # <-- tells Celery to import this module at startup
    ],
)

celery_app.conf.task_routes = {
    "app.workers.tasks.*": {"queue": "pdf-tasks"}
}
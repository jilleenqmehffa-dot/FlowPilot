import os

from celery import Celery

app = Celery(
    "flowpilot",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
)


@app.task
def ping() -> str:
    return "pong"

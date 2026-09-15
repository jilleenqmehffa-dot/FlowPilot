from celery import Celery

from backend.app.core.config import get_settings

settings = get_settings()

app = Celery(
    "flowpilot",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)


@app.task
def ping() -> str:
    return "pong"

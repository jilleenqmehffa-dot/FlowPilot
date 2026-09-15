from celery import Celery

from backend.app.core.config import get_settings
from backend.app.core.log import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

app = Celery(
    "flowpilot",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)


@app.task
def ping() -> str:
    return "pong"

from fastapi import FastAPI

from backend.app.core.config import get_settings
from backend.app.core.log import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(title=settings.app_name)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

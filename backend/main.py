from fastapi import FastAPI

app = FastAPI(title="FlowPilot")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

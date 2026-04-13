from fastapi import FastAPI

from config import settings
from routes.pipeline import router as pipeline_router

app = FastAPI(title=settings.app_name)
app.include_router(pipeline_router, prefix=settings.api_prefix)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

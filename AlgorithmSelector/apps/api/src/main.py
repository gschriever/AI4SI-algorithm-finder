from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import traceback
import logging

from config import settings
from routes.pipeline import router as pipeline_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    logger.error(f"Internal Server Error: {exc}\n{tb}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc), "traceback": tb},
    )

app.include_router(pipeline_router, prefix=settings.api_prefix)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

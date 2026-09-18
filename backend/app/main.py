"""Lightweight API entry point for the reusable school platform."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .settings import get_settings

settings = get_settings()
app = FastAPI(title="Reusable School Platform API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Confirm that the API process is running."""
    return {"status": "ok", "service": "school-platform-api"}



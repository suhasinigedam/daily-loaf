from fastapi import FastAPI

from app.api.routes import health
from app.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(title="Daily Loaf API", version="0.1.0")
    app.state.settings = settings
    app.include_router(health.router, prefix="/api/v1")
    return app
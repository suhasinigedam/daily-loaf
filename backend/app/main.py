from fastapi import FastAPI

from app.api.errors import install_error_handlers
from app.api.middleware import RequestIdMiddleware
from app.api.routes import health
from app.config import Settings
from app.logging_config import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.log_level)

    app = FastAPI(title="Daily Loaf API", version="0.1.0")
    app.state.settings = settings
    app.add_middleware(RequestIdMiddleware)
    install_error_handlers(app)
    app.include_router(health.router, prefix="/api/v1")
    return app

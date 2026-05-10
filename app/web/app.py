from core.config import get_settings
from core.logging import configure_logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.web.csrf import CSRFMiddleware
from app.web.discovery import discover_module_routers
from app.web.routes import auth, guilds, health


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title="Modular Discord Dashboard Bot API", version="0.1.0")
    app.add_middleware(CSRFMiddleware, settings=settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-CSRF-Token"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(guilds.router)
    for router in discover_module_routers():
        app.include_router(router)
    return app

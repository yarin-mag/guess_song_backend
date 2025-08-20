from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.middlewares.auth import AuthMiddleware
from app.middlewares.request_logger import LoggingMiddleware
from app.middlewares.rate_limiter import RateLimiterMiddleware
from app.middlewares.request_id import RequestIdMiddleware
from app.middlewares.error_handler import app_exception_handler
from app.shared.exceptions import AppException
from app.core.logger import setup_logging
from dotenv import load_dotenv
load_dotenv()

import os

IS_RUNNING_LOCAL = os.getenv("IS_RUNNING_LOCAL") == "true"

def create_app(
    title: str = "API",
    version: str = "0.1",
    routers: list = None,
    with_static: bool = False,
    with_middlewares: bool = True
) -> FastAPI:
    setup_logging()
    app = FastAPI(title=title, version=version)

    if with_middlewares:
        app.add_middleware(RequestIdMiddleware)
        app.add_middleware(AuthMiddleware)
        app.add_middleware(LoggingMiddleware)
        app.add_middleware(RateLimiterMiddleware, max_requests=1000 if IS_RUNNING_LOCAL else 10, window_seconds=60) # TODO: uncomment
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["https://localhost:5173", "http://localhost:5173"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    if with_static:
        app.mount("/static", StaticFiles(directory=os.path.join("app", "static")), name="static")

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    if routers:
        for router in routers:
            app.include_router(router)

    app.add_exception_handler(AppException, app_exception_handler)

    return app

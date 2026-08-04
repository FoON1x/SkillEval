from fastapi import FastAPI

from skill_eval.ingest.api import router as ingest_router
from skill_eval.runner.api import router as runner_router

APP_NAME = "skilleval-api"
__version__ = "0.1.0"


def create_app() -> FastAPI:
    app = FastAPI(title=APP_NAME, version=__version__)
    app.include_router(ingest_router)
    app.include_router(runner_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/")
    def root() -> dict[str, str]:
        return {"service": APP_NAME}

    return app
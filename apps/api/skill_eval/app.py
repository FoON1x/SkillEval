from fastapi import FastAPI

APP_NAME = "skilleval-api"
__version__ = "0.1.0"


def create_app() -> FastAPI:
    app = FastAPI(title=APP_NAME, version=__version__)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/")
    def root() -> dict[str, str]:
        return {"service": APP_NAME}

    return app
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from skill_eval.eval.api import router as eval_router
from skill_eval.fs import router as fs_router
from skill_eval.ingest.api import router as ingest_router
from skill_eval.judge.api import router as judge_router
from skill_eval.judge.client import LLMClient
from skill_eval.runner.api import router as runner_router
from skill_eval.store.api import router as store_router
from skill_eval.store.repository import Store

APP_NAME = "skilleval-api"
__version__ = "0.2.0"

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def create_app(store: Store | None = None, judge_client: LLMClient | None = None) -> FastAPI:
    app = FastAPI(title=APP_NAME, version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.store = store or Store.default()
    app.state.judge_client = judge_client or LLMClient()
    app.include_router(ingest_router)
    app.include_router(runner_router)
    app.include_router(store_router)
    app.include_router(eval_router)
    app.include_router(judge_router)
    app.include_router(fs_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/")
    def root() -> dict[str, str]:
        return {"service": APP_NAME}

    return app
from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from kagamium.api import create_api_router
from kagamium.config import Settings, settings
from kagamium.database import Database


def _with_api_prefix(api_prefix: str, suffix: str) -> str:
    return f"{api_prefix}{suffix}" if api_prefix else suffix


def create_app(app_settings: Settings | None = None) -> FastAPI:
    resolved_settings = app_settings or settings
    resolved_settings.uploads_dir.mkdir(parents=True, exist_ok=True)

    database = Database(resolved_settings.database_path)
    database.initialize()

    app = FastAPI(
        title="Kagamium Backend",
        docs_url=_with_api_prefix(resolved_settings.api_prefix, "/docs"),
        redoc_url=_with_api_prefix(resolved_settings.api_prefix, "/redoc"),
        openapi_url=_with_api_prefix(resolved_settings.api_prefix, "/openapi.json"),
        swagger_ui_parameters={"persistAuthorization": True},
    )
    app.state.settings = resolved_settings
    app.state.database = database
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved_settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(create_api_router(resolved_settings, database))
    return app


app = create_app()


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=settings.backend_port)


if __name__ == "__main__":
    main()

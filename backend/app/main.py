import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.api.v1.projects import router as projects_router
from app.api.v1.servers import router as servers_router
from app.api.v1.webhooks import router as webhooks_router
from app.db.database import Base, engine


def ensure_sqlite_compatibility_schema(connection: Connection) -> None:
    if connection.dialect.name != "sqlite":
        return

    table_columns = {
        table_name: {
            row[1]
            for row in connection.execute(text(f"PRAGMA table_info({table_name})"))
        }
        for table_name in ("servers", "projects")
    }

    if "servers" in table_columns and "is_active" not in table_columns["servers"]:
        connection.execute(
            text("ALTER TABLE servers ADD COLUMN is_active BOOLEAN DEFAULT NULL")
        )

    if "projects" in table_columns and "use_https" not in table_columns["projects"]:
        connection.execute(
            text("ALTER TABLE projects ADD COLUMN use_https BOOLEAN NOT NULL DEFAULT 0")
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # При старте приложения (для dev) создаем таблицы БД
    async with engine.begin() as conn:
        # В проде добавить alembic migrations
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(ensure_sqlite_compatibility_schema)
    yield


def resolve_frontend_dist() -> Path | None:
    current_file = Path(__file__).resolve()
    candidate_paths = [
        current_file.parents[2] / "frontend" / "dist",
    ]

    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root is not None:
        candidate_paths.append(Path(bundle_root) / "frontend" / "dist")

    for path in candidate_paths:
        if path.exists():
            return path

    return None


def create_app(frontend_dist: Path | None = None) -> FastAPI:
    app = FastAPI(title="Deplock Control Plane API", lifespan=lifespan)

    # Настройка CORS для взаимодействия с Frontend
    app.add_middleware(
        cast(Any, CORSMiddleware),
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Регистрация v1 API роутеров
    app.include_router(projects_router, prefix="/api/v1")
    app.include_router(servers_router, prefix="/api/v1")
    app.include_router(webhooks_router, prefix="/api/v1")

    @app.get("/health", tags=["system"])
    async def health_check():
        return {"status": "ok"}

    dist_path = frontend_dist or resolve_frontend_dist()
    if dist_path is not None:
        resolved_dist_path = dist_path.resolve()

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_frontend(full_path: str):
            if full_path.startswith(("api/", "health")):
                raise HTTPException(status_code=404)

            requested_path = (resolved_dist_path / full_path).resolve()
            if (
                full_path
                and resolved_dist_path in requested_path.parents
                and requested_path.is_file()
            ):
                return FileResponse(requested_path)

            return FileResponse(resolved_dist_path / "index.html")

    return app


app = create_app()

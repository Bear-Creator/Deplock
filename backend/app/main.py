from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, cast

from app.api.v1.projects import router as projects_router
from app.api.v1.servers import router as servers_router
from app.api.v1.webhooks import router as webhooks_router
from app.db.database import Base, engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


@asynccontextmanager
async def lifespan(app: FastAPI):
    # При старте приложения (для dev) создаем таблицы БД
    async with engine.begin() as conn:
        # В проде тут должны быть alembic migrations
        await conn.run_sync(Base.metadata.create_all)
    yield


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


# Serve frontend built files if present (pywebview packaging will include frontend/dist)
dist_path = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if dist_path.exists():
    app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="frontend")


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok"}

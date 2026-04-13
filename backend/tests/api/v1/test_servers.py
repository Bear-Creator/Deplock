from collections.abc import AsyncGenerator

import pytest
from app.api.dependencies.db import get_db_session
from app.db.database import Base
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Тестовая in-memory БД
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

mock_async_session_maker = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db_session() -> AsyncGenerator[AsyncSession]:
    async with mock_async_session_maker() as session:
        yield session


app.dependency_overrides[get_db_session] = override_get_db_session


@pytest.fixture(autouse=True)
async def prepare_database():
    """Создаёт и удаляет таблицы перед каждым тестом."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_create_server():
    """Тест успешного создания сервера."""
    payload = {"name": "test-box-1", "ip_address": "12.34.56.78", "ssh_user": "ubuntu"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/api/v1/servers/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-box-1"
    assert data["ip_address"] == "12.34.56.78"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_server_duplicate_name():
    """Тест проверки на дубликат имени (unique constraint)."""
    payload = {"name": "unique-box", "ip_address": "8.8.8.8"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        await ac.post("/api/v1/servers/", json=payload)
        # Отправляем тот же payload
        response = await ac.post("/api/v1/servers/", json=payload)

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_servers():
    """Тест получения списка серверов."""
    payload = {"name": "list-box-1", "ip_address": "1.1.1.1"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        await ac.post("/api/v1/servers/", json=payload)
        response = await ac.get("/api/v1/servers/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "list-box-1"

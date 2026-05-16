import pytest
from app.main import app, create_app, ensure_sqlite_compatibility_schema
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text


@pytest.mark.asyncio
async def test_health_check():
    # Проверяем инициализацию базового скелета и статус сервиса
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_frontend_dist_is_served_when_configured(tmp_path):
    index_file = tmp_path / "index.html"
    index_file.write_text("<html><body>Deplock UI</body></html>", encoding="utf-8")

    test_app = create_app(frontend_dist=tmp_path)

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        response = await ac.get("/")
        nested_response = await ac.get("/servers")

    assert response.status_code == 200
    assert "Deplock UI" in response.text
    assert nested_response.status_code == 200
    assert "Deplock UI" in nested_response.text


@pytest.mark.asyncio
async def test_unknown_api_route_does_not_fall_back_to_frontend(tmp_path):
    index_file = tmp_path / "index.html"
    index_file.write_text("<html><body>Deplock UI</body></html>", encoding="utf-8")

    test_app = create_app(frontend_dist=tmp_path)

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/unknown")

    assert response.status_code == 404


def test_sqlite_compatibility_schema_adds_missing_columns(tmp_path):
    database_path = tmp_path / "compat.db"
    engine = create_engine(f"sqlite:///{database_path}")

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE servers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    ssh_user TEXT NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    image TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    status TEXT NOT NULL,
                    container_id TEXT NULL,
                    server_id TEXT NOT NULL
                )
                """
            )
        )

        ensure_sqlite_compatibility_schema(connection)

        server_columns = {
            row[1] for row in connection.execute(text("PRAGMA table_info(servers)"))
        }
        project_columns = {
            row[1] for row in connection.execute(text("PRAGMA table_info(projects)"))
        }

    assert "is_active" in server_columns
    assert "use_https" in project_columns

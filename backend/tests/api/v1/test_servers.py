import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient


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

import uuid

import pytest
from app.main import app as fastapi_app
from httpx import ASGITransport, AsyncClient


# Простейший mock для RemoteDockerClient
class MockRemoteDockerClient:
    def deploy_project(self, image: str, project_name: str, domain: str):
        # Эмуляция успешного деплоя
        if "error" in project_name:
            import docker

            raise docker.errors.APIError("Mocked Docker Error")
        return {"container_id": "success-fake-id", "status": "created"}


def override_get_docker_client(server):
    return MockRemoteDockerClient()


# Убираем dependency_overrides так как get_docker_client больше не Depends(), а обычный вызов функции внутри create_project


@pytest.fixture(autouse=True)
def mock_docker_factory(monkeypatch):
    """Подменяем вызов фабрики клиента в роутерах"""
    monkeypatch.setattr(
        "app.api.v1.projects.get_docker_client", override_get_docker_client
    )


@pytest.mark.asyncio
async def test_create_project_success():
    """Тест успешного создания проекта и БД записи"""
    # Создаем сервер перед деплоем
    server_payload = {
        "name": "target-server",
        "ip_address": "12.34.56.78",
        "ssh_user": "root",
    }
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as ac:
        res_server = await ac.post("/api/v1/servers/", json=server_payload)
        server_id = res_server.json()["id"]

        payload = {
            "name": "my-cool-project",
            "image": "nginx:alpine",
            "domain": "myproject.dev.local",
            "server_id": server_id,
        }
        response = await ac.post("/api/v1/projects/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "my-cool-project"
    assert data["container_id"] == "success-fake-id"
    assert data["status"] == "created"
    assert data["server_id"] == server_id


@pytest.mark.asyncio
async def test_create_project_docker_error():
    server_payload = {"name": "target-server-2", "ip_address": "11.11.11.11"}
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as ac:
        res_server = await ac.post("/api/v1/servers/", json=server_payload)
        server_id = res_server.json()["id"]

        payload = {
            "name": "error-project",
            "image": "nginx:alpine",
            "domain": "error.dev.local",
            "server_id": server_id,
        }
        response = await ac.post("/api/v1/projects/", json=payload)

    # Ожидаем 500 из-за обработки в except блоке
    assert response.status_code == 500
    assert "Docker API error: Mocked Docker Error" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_project_no_server():
    """Тест 404 ошибки если сервер не найден"""
    payload = {
        "name": "no-server-project",
        "image": "nginx:alpine",
        "domain": "no.dev.local",
        "server_id": str(uuid.uuid4()),
    }
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as ac:
        response = await ac.post("/api/v1/projects/", json=payload)

    assert response.status_code == 404

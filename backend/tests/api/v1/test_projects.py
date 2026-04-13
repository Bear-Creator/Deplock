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

    def remove_project(self, container_id: str):
        # Эмуляция успешного удаления
        if "error" in container_id:
            import docker

            raise docker.errors.APIError("Mocked Docker Error on remove")
        return True

    def get_container_logs(self, container_id: str, tail: int = 100) -> str:
        if "error" in container_id:
            return "Failed to get logs for container error: test"
        return "Fake docker logs output"

    def pull_image(self, image: str):
        if "error" in image:
            import docker

            raise docker.errors.APIError("Mocked Docker Error on pull")
        return True


def override_get_docker_client(server):
    return MockRemoteDockerClient()


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


@pytest.mark.asyncio
async def test_get_projects():
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as ac:
        res = await ac.get("/api/v1/projects/")
        assert res.status_code == 200
        assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_delete_project():
    server_payload = {"name": "target-server-del", "ip_address": "8.8.8.8"}
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as ac:
        res_server = await ac.post("/api/v1/servers/", json=server_payload)
        server_id = res_server.json()["id"]

        payload = {
            "name": "del-project",
            "image": "nginx:alpine",
            "domain": "del.dev.local",
            "server_id": server_id,
        }
        res_proj = await ac.post("/api/v1/projects/", json=payload)
        proj_id = res_proj.json()["id"]

        del_res = await ac.delete(f"/api/v1/projects/{proj_id}")
        assert del_res.status_code == 204

        get_res = await ac.get("/api/v1/projects/")
        assert proj_id not in [p["id"] for p in get_res.json()]


@pytest.mark.asyncio
async def test_get_project_logs():
    server_payload = {"name": "target-server-logs", "ip_address": "8.8.8.8"}
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as ac:
        res_server = await ac.post("/api/v1/servers/", json=server_payload)
        server_id = res_server.json()["id"]

        payload = {
            "name": "logs-project",
            "image": "nginx:alpine",
            "domain": "logs.dev.local",
            "server_id": server_id,
        }
        res_proj = await ac.post("/api/v1/projects/", json=payload)
        proj_id = res_proj.json()["id"]

        logs_res = await ac.get(f"/api/v1/projects/{proj_id}/logs")
        assert logs_res.status_code == 200
        assert logs_res.json()["logs"] == "Fake docker logs output"

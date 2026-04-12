import pytest
from app.api.dependencies.docker import get_docker_client
from app.main import app
from httpx import ASGITransport, AsyncClient


# Простейший mock для RemoteDockerClient
class MockRemoteDockerClient:
    def deploy_project(self, image: str, project_name: str, domain: str):
        # Эмуляция успешного деплоя
        if "error" in project_name:
            import docker

            raise docker.errors.APIError("Mocked Docker Error")
        return {"container_id": "success-fake-id", "status": "created"}


def override_get_docker_client():
    return MockRemoteDockerClient()


app.dependency_overrides[get_docker_client] = override_get_docker_client


@pytest.mark.asyncio
async def test_create_project_success():
    payload = {
        "name": "my-cool-project",
        "image": "nginx:alpine",
        "domain": "myproject.dev.local",
    }
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/api/v1/projects/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Project deployed successfully"
    assert data["data"]["container_id"] == "success-fake-id"


@pytest.mark.asyncio
async def test_create_project_docker_error():
    payload = {
        "name": "error-project",
        "image": "nginx:alpine",
        "domain": "error.dev.local",
    }
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/api/v1/projects/", json=payload)

    # Ожидаем 500 из-за обработки в except блоке
    assert response.status_code == 500
    assert "Docker API error: Mocked Docker Error" in response.json()["detail"]

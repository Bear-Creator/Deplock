import uuid

import pytest
from app.main import app as fastapi_app
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_github_webhook_wrong_event():
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as ac:
        res = await ac.post(
            f"/api/v1/webhooks/github/{uuid.uuid4()}",
            headers={"x-github-event": "ping"},
        )
        assert res.status_code == 200
        assert "Ignored event" in res.json()["message"]


@pytest.mark.asyncio
async def test_github_webhook_push_not_found():
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as ac:
        res = await ac.post(
            f"/api/v1/webhooks/github/{uuid.uuid4()}",
            headers={"x-github-event": "push"},
        )
        assert res.status_code == 404
        assert "Project" in res.json()["detail"]


@pytest.mark.asyncio
async def test_github_webhook_push_success():
    server_payload = {"name": "wh-server", "ip_address": "8.8.8.8"}
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as ac:
        res_server = await ac.post("/api/v1/servers/", json=server_payload)
        server_id = res_server.json()["id"]

        payload = {
            "name": "wh-project",
            "image": "nginx:alpine",
            "domain": "wh.dev.local",
            "server_id": server_id,
        }
        res_proj = await ac.post("/api/v1/projects/", json=payload)
        proj_id = res_proj.json()["id"]

        res = await ac.post(
            f"/api/v1/webhooks/github/{proj_id}", headers={"x-github-event": "push"}
        )
        assert res.status_code == 200
        assert res.json()["message"] == "Redeployed successfully"
        assert "container_id" in res.json()


@pytest.fixture(autouse=True)
def mock_docker_factory(monkeypatch):
    """Подменяем вызов фабрики клиента в роутерах"""
    from tests.api.v1.test_projects import override_get_docker_client

    monkeypatch.setattr(
        "app.api.v1.webhooks.get_docker_client", override_get_docker_client
    )
    monkeypatch.setattr(
        "app.api.v1.projects.get_docker_client", override_get_docker_client
    )

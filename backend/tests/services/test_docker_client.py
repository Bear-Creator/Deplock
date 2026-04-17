from unittest.mock import MagicMock, patch

import pytest
from app.services.docker_client import RemoteDockerClient


@pytest.fixture
def mock_docker_lib():
    with patch("app.services.docker_client.docker.DockerClient") as mock_client:
        yield mock_client


def test_remote_docker_client_initialization(mock_docker_lib):
    host = "192.168.1.100"
    user = "admin"

    # Проверка, что класс корректно собирает SSH строку
    client = RemoteDockerClient(host=host, user=user)

    assert client.base_url == "ssh://admin@192.168.1.100"
    mock_docker_lib.assert_called_once_with(
        base_url="ssh://admin@192.168.1.100", use_ssh_client=True
    )


def test_deploy_project_sends_correct_labels(mock_docker_lib):
    client = RemoteDockerClient(host="localhost", user="root")

    # Создаем Mock-ответ
    mock_container = MagicMock()
    mock_container.id = "mock-id-123"
    mock_container.status = "created"

    # Настраиваем возвращаемое значение метода run
    mock_docker_lib.return_value.containers.run.return_value = mock_container

    # Выполняем деплой проекта
    project_name = "test-project"
    domain = "test.example.com"
    image = "nginx:alpine"

    result = client.deploy_project(
        image=image, project_name=project_name, domain=domain
    )

    # Assert
    assert result == {"container_id": "mock-id-123", "status": "created"}

    # Проверка что правильные Labels для Traefik переданы при запуске (ADR-002)
    mock_docker_lib.return_value.containers.run.assert_called_once_with(
        image=image,
        name=project_name,
        labels={
            "traefik.enable": "true",
            "traefik.http.routers.test-project.rule": "Host(`test.example.com`)",
            "traefik.http.routers.test-project.entrypoints": "websecure",
            "traefik.http.routers.test-project.tls.certresolver": "myresolver",
            "traefik.http.services.test-project.loadbalancer.server.port": "80",
        },
        network="traefik-net",
        detach=True,
        restart_policy={"Name": "unless-stopped"},
    )

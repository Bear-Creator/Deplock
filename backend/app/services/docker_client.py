import subprocess
import sys
from typing import Any

import docker
import docker.errors

# Patch subprocess.Popen on Windows to prevent SSH terminal pop-ups
if sys.platform == "win32":

    class PatchedPopen(subprocess.Popen):
        def __init__(self, *args, **kwargs):
            if "creationflags" not in kwargs:
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            super().__init__(*args, **kwargs)

    subprocess.Popen = PatchedPopen  # type: ignore


class RemoteDockerClient:
    """Абстракция над docker-py для связи с докер-демоном ресурса через SSH."""

    def __init__(self, host: str, user: str = "root"):
        # Используем SSH transport, так как открывать Docker daemon по TCP без TLS небезопасно.
        # Ожидается, что на управляющей машине настроен SSH-доступ к целевому серверу.
        self.base_url = f"ssh://{user}@{host}"
        self.client = docker.DockerClient(base_url=self.base_url, use_ssh_client=True)

    def deploy_project(
        self, image: str, project_name: str, domain: str, use_https: bool = False
    ) -> dict[str, Any]:
        """Осуществляет развертывание контейнера из переданного образа и настраивает маршрутизацию."""
        # Удаляем существующий контейнер с таким именем, если он есть
        self.remove_project(project_name)

        # Для Traefik требуется указать labels на контейнере (ADR-002: Service Discovery)
        labels = {
            "traefik.enable": "true",
            f"traefik.http.routers.{project_name}.rule": f"Host(`{domain}`)",
            f"traefik.http.services.{project_name}.loadbalancer.server.port": "80",
        }

        if use_https:
            labels[f"traefik.http.routers.{project_name}.entrypoints"] = "websecure"
            labels[f"traefik.http.routers.{project_name}.tls.certresolver"] = (
                "myresolver"
            )
        else:
            labels[f"traefik.http.routers.{project_name}.entrypoints"] = "web"

        # Запускаем контейнер в detached режиме
        container = self.client.containers.run(
            image=image,
            name=project_name,
            labels=labels,
            network="traefik-net",  # Ожидаем, что Ansible уже создал сеть для Traefik
            detach=True,
            restart_policy={"Name": "unless-stopped"},
        )

        return {"container_id": container.id, "status": container.status}

    def remove_project(self, container_id: str) -> bool:
        """Останавливает и удаляет контейнер проекта по его ID."""
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            container.remove()
            return True
        except docker.errors.NotFound:
            # Если контейнер уже удален или не найден - считаем операцию успешной
            return True

    def cleanup_node(self, project_identifiers: list[str]) -> None:
        """Очищает сервер: удаляет все переданные проекты, а также Traefik и его сеть."""
        # 1. Удаляем все контейнеры-проекты
        for identifier in project_identifiers:
            self.remove_project(identifier)

        # 2. Удаляем Traefik
        self.remove_project("traefik")

        # 3. Удаляем сеть traefik-net
        try:
            net = self.client.networks.get("traefik-net")
            net.remove()
        except docker.errors.NotFound:
            pass

    def get_container_logs(self, container_id: str, tail: int = 100) -> str:
        """Получает логи указанного контейнера."""
        try:
            container = self.client.containers.get(container_id)
            # Возвращаем декодированные логи (строка)
            return container.logs(tail=tail, stdout=True, stderr=True).decode("utf-8")
        except docker.errors.NotFound:
            return f"Container {container_id} not found."
        except Exception as e:
            return f"Failed to get logs for container {container_id}: {e!s}"

    def pull_image(self, image: str) -> None:
        """Скачивает последнюю (или указанную) версию образа."""
        self.client.images.pull(image)

    def is_available(self, timeout: int = 5) -> tuple[bool, str | None]:
        """Проверяет доступность Docker daemon на удалённом хосте.

        Возвращает пару (available, details). Если доступен, details = None.
        """
        try:
            # docker-py предоставляет метод ping() для проверки API
            self.client.ping()
            return True, None
        except Exception as e:
            return False, str(e)

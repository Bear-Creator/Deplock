from typing import Any

import docker


class RemoteDockerClient:
    """Абстракция над docker-py для связи с докер-демоном ресурса через SSH."""

    def __init__(self, host: str, user: str = "root"):
        # Используем SSH transport, так как открывать Docker daemon по TCP без TLS небезопасно.
        # Ожидается, что на управляющей машине настроен SSH-доступ к целевому серверу.
        self.base_url = f"ssh://{user}@{host}"
        self.client = docker.DockerClient(base_url=self.base_url)

    def deploy_project(
        self, image: str, project_name: str, domain: str
    ) -> dict[str, Any]:
        """Осуществляет развертывание контейнера из переданного образа и настраивает маршрутизацию."""
        # Для Traefik требуется указать labels на контейнере (ADR-002: Service Discovery)
        labels = {
            "traefik.enable": "true",
            f"traefik.http.routers.{project_name}.rule": f"Host(`{domain}`)",
            f"traefik.http.routers.{project_name}.entrypoints": "websecure",
            f"traefik.http.routers.{project_name}.tls.certresolver": "myresolver",
            f"traefik.http.services.{project_name}.loadbalancer.server.port": "80",
        }

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

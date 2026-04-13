from app.db.models import Server
from app.services.docker_client import RemoteDockerClient


def get_docker_client(server: Server) -> RemoteDockerClient:
    """
    Фабрика создания клиента Docker для указанного сервера.
    """
    return RemoteDockerClient(host=server.ip_address, user=server.ssh_user)

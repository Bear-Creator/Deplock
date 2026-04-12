from app.services.docker_client import RemoteDockerClient


def get_docker_client() -> RemoteDockerClient:
    """
    Фабрика для инъекции зависимости RemoteDockerClient.
    Пока захардкожено, позже параметры хоста будут браться из базы данных (сущность Server).
    """
    # TODO: Получать credentials из контекста запроса (ID сервера)
    return RemoteDockerClient(host="localhost", user="root")

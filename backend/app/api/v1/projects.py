import docker
from app.api.dependencies.docker import get_docker_client
from app.schemas.projects import ProjectCreate
from app.services.docker_client import RemoteDockerClient
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    docker_client: RemoteDockerClient = Depends(get_docker_client),
):
    """
    Endpoint для деплоя нового проекта (контейнера).
    """
    try:
        # Бизнес-логика изоляции деплоя в сервисный слой
        result = docker_client.deploy_project(
            image=project_data.image,
            project_name=project_data.name,
            domain=project_data.domain,
        )
        return {"message": "Project deployed successfully", "data": result}
    except docker.errors.APIError as e:
        # Ловим специфичные ошибки Docker SDK, возвращаем понятный HTTP статус
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Docker API error: {e}",
        ) from e
    except Exception as e:
        # Ловим остальные ошибки (сетевые, SSH)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deploy project: {e!s}",
        ) from e

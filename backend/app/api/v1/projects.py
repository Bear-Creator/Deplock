import docker
from app.api.dependencies.db import get_db_session
from app.api.dependencies.docker import get_docker_client
from app.db.models import Project, Server
from app.schemas.projects import ProjectCreate, ProjectRead
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Endpoint для деплоя нового проекта (контейнера).
    """

    server = await session.get(Server, project_data.server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with ID {project_data.server_id} not found.",
        )

    # Инициализация Remote docker client для выбранного сервера
    docker_client = get_docker_client(server)

    try:
        # Бизнес-логика изоляции деплоя в сервисный слой
        result = docker_client.deploy_project(
            image=project_data.image,
            project_name=project_data.name,
            domain=project_data.domain,
        )

        # Сохранение статуса в БД
        new_project = Project(
            name=project_data.name,
            image=project_data.image,
            domain=project_data.domain,
            server_id=server.id,
            container_id=result.get("container_id"),
            status=result.get("status", "running"),
        )
        session.add(new_project)
        await session.commit()
        await session.refresh(new_project)

        return new_project
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

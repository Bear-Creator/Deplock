import uuid

import docker
from app.api.dependencies.db import get_db_session
from app.api.dependencies.docker import get_docker_client
from app.db.models import Project, Server
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/github/{project_id}", status_code=status.HTTP_200_OK)
async def github_webhook(
    project_id: uuid.UUID,
    x_github_event: str | None = Header(None),
    x_hub_signature_256: str | None = Header(None),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Webhook для получения уведомлений от GitHub и автоматического редеплоя проекта.
    """
    if x_github_event and x_github_event != "push":
        return {"message": f"Ignored event: {x_github_event}"}

    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found.",
        )

    server = await session.get(Server, project.server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {project.server_id} not found.",
        )

    docker_client = get_docker_client(server)

    try:
        if hasattr(docker_client, "pull_image"):
            docker_client.pull_image(project.image)

        if project.container_id:
            docker_client.remove_project(project.container_id)

        result = docker_client.deploy_project(
            image=project.image,
            project_name=project.name,
            domain=project.domain,
        )

        project.container_id = str(result.get("container_id", ""))
        project.status = str(result.get("status", "running"))
        await session.commit()
        await session.refresh(project)
    except docker.errors.APIError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Docker API error during redeploy: {e}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to redeploy project: {e!s}",
        ) from e

    return {"message": "Redeployed successfully", "container_id": project.container_id}

import contextlib
import logging
import uuid
from typing import Any

from app.api.dependencies.db import get_db_session
from app.db.models import Server
from app.schemas.servers import ServerCreate, ServerRead
from app.services.bootstrap_service import bootstrap_server_via_ssh
from app.services.docker_client import RemoteDockerClient
from app.services.ssh_setup import install_public_key_via_password
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/servers", tags=["servers"])


@router.post("/", response_model=ServerRead, status_code=status.HTTP_201_CREATED)
async def create_server(
    server_in: ServerCreate, session: AsyncSession = Depends(get_db_session)
) -> Any:
    """Создаёт новую запись о целевом сервере для деплоя"""

    # Есть сервер с тем же именем
    stmt = select(Server).where(Server.name == server_in.name)
    result = await session.execute(stmt)
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Server with name {server_in.name} already exists.",
        )

    # Если передан пароль, устанавливаем публичный SSH ключ
    if server_in.initial_password:
        try:
            # Выполняется синхронно, но для простых операций это терпимо;
            # можно было бы завернуть в run_in_executor
            install_public_key_via_password(
                ip_address=str(server_in.ip_address),
                ssh_user=server_in.ssh_user,
                password=server_in.initial_password,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to setup SSH key: {e}",
            ) from e

    # Сохраняем как string для БД
    new_server = Server(
        name=server_in.name,
        ip_address=str(server_in.ip_address),
        ssh_user=server_in.ssh_user,
    )

    session.add(new_server)
    await session.commit()
    await session.refresh(new_server)

    # Newly created server is not active until bootstrapped

    with contextlib.suppress(Exception):
        new_server.is_active = False

    return new_server


@router.get("/", response_model=list[ServerRead])
async def list_servers(session: AsyncSession = Depends(get_db_session)) -> Any:
    """Возвращает список всех серверов"""
    stmt = select(Server).options(selectinload(Server.projects))
    result = await session.execute(stmt)
    servers = result.scalars().all()

    # Compute is_active based on projects (container_id present or running status)
    for s in servers:
        try:
            # First, try to check Docker daemon availability via SSH
            try:
                remote_client = RemoteDockerClient(host=s.ip_address, user=s.ssh_user)
                available, _details = remote_client.is_available()
                if available:
                    s.is_active = True
                    continue
            except Exception:
                # If docker client creation/ping fails, fall back to projects heuristics
                pass

            active = any(
                (getattr(p, "container_id", None) is not None)
                or (getattr(p, "status", None) == "running")
                for p in s.projects
            )
            s.is_active = bool(active)
        except Exception:
            s.is_active = None

    return list(servers)


@router.get("/{server_id}", response_model=ServerRead)
async def get_server(
    server_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)
) -> Any:
    """Получает информацию о конкретном сервере"""
    stmt = (
        select(Server)
        .options(selectinload(Server.projects))
        .where(Server.id == server_id)
    )
    result = await session.execute(stmt)
    server = result.scalars().first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    try:
        try:
            try:
                remote_client = RemoteDockerClient(
                    host=server.ip_address, user=server.ssh_user
                )
                available, _details = remote_client.is_available()
                if available:
                    server.is_active = True
                else:
                    active = any(
                        (getattr(p, "container_id", None) is not None)
                        or (getattr(p, "status", None) == "running")
                        for p in server.projects
                    )
                    server.is_active = bool(active)
            except Exception:
                active = any(
                    (getattr(p, "container_id", None) is not None)
                    or (getattr(p, "status", None) == "running")
                    for p in server.projects
                )
                server.is_active = bool(active)
        except Exception:
            server.is_active = None
    except Exception:
        server.is_active = None

    return server


@router.post("/{server_id}/bootstrap", status_code=status.HTTP_200_OK)
async def bootstrap_server(
    server_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)
) -> dict:
    """Подготавливает сервер для работы"""
    server = await session.get(Server, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    try:
        output = await bootstrap_server_via_ssh(server.ip_address, server.ssh_user)
        return {
            "status": "success",
            "message": "Server configured successfully.",
            "details": output,
        }
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(
    server_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)
) -> None:
    """Удаляет сервер по его ID, предварительно очищая удаленные контейнеры"""
    stmt = (
        select(Server)
        .options(selectinload(Server.projects))
        .where(Server.id == server_id)
    )
    result = await session.execute(stmt)
    server = result.scalars().first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    # Пытаемся удалить объекты на удаленном узле
    try:
        remote_client = RemoteDockerClient(host=server.ip_address, user=server.ssh_user)
        project_identifiers = [
            proj.container_id if proj.container_id else proj.name
            for proj in server.projects
        ]
        remote_client.cleanup_node(project_identifiers)
    except Exception as e:
        logger.warning(
            f"Failed to cleanup remote containers on server {server.ip_address}: {e}"
        )
        # Даже если удаленный сервер недоступен, мы продолжаем процесс удаления из БД

    await session.delete(server)
    await session.commit()
    return

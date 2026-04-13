import uuid
from typing import Any

from app.api.dependencies.db import get_db_session
from app.db.models import Server
from app.schemas.servers import ServerCreate, ServerRead
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/servers", tags=["servers"])


@router.post("/", response_model=ServerRead, status_code=status.HTTP_201_CREATED)
async def create_server(
    server_in: ServerCreate, session: AsyncSession = Depends(get_db_session)
) -> Any:
    """Создаёт новую запись о целевом сервере для деплоя."""

    # Проверка на существование сервера с таким же именем
    stmt = select(Server).where(Server.name == server_in.name)
    result = await session.execute(stmt)
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Server with name {server_in.name} already exists.",
        )

    # Сохраняем как string для БД
    new_server = Server(
        name=server_in.name,
        ip_address=str(server_in.ip_address),
        ssh_user=server_in.ssh_user,
    )

    session.add(new_server)
    await session.commit()
    await session.refresh(new_server)

    return new_server


@router.get("/", response_model=list[ServerRead])
async def list_servers(session: AsyncSession = Depends(get_db_session)) -> Any:
    """Возвращает список всех серверов."""
    stmt = select(Server)
    result = await session.execute(stmt)
    servers = result.scalars().all()
    # Преобразовываем к Pydantic-моделям (from_attributes = True)
    return list(servers)


@router.get("/{server_id}", response_model=ServerRead)
async def get_server(
    server_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)
) -> Any:
    """Получает информацию о конкретном сервере."""
    server = await session.get(Server, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server

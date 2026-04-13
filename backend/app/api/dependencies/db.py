from collections.abc import AsyncGenerator

from app.db.database import async_session_maker
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """Dependency, отдающая асинхронную сессию БД."""
    async with async_session_maker() as session:
        yield session

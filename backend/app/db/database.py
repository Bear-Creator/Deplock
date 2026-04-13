from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Искомая строка подключения (SQLite для DEV-среды)
DATABASE_URL = "sqlite+aiosqlite:///./deplock.db"

# Создаем асинхронный движок
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},  # Специфично для SQLite
)

# Асинхронная сессия
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass

import uuid

from app.db.database import Base
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Server(Base):
    __tablename__ = "servers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    ip_address: Mapped[str] = mapped_column(String(50))
    ssh_user: Mapped[str] = mapped_column(String(50), default="root")

    # One-to-Many к Project
    projects: Mapped[list[Project]] = relationship(
        "Project", back_populates="server", cascade="all, delete-orphan"
    )


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    image: Mapped[str] = mapped_column(String(200))
    domain: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="created")
    container_id: Mapped[str] = mapped_column(String(100), nullable=True)

    server_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("servers.id"))
    server: Mapped[Server] = relationship("Server", back_populates="projects")

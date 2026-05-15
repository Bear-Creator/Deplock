import uuid

from pydantic import BaseModel, ConfigDict, Field


class ProjectBase(BaseModel):
    name: str = Field(..., title="Название проекта", max_length=100)
    image: str = Field(..., title="Docker Image для деплоя", max_length=200)
    domain: str = Field(..., title="Домен для маршрутизации Traefik", max_length=255)
    server_id: uuid.UUID = Field(..., title="ID целевого сервера")
    use_https: bool = Field(False, title="Включить HTTPS")


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: uuid.UUID
    status: str
    container_id: str | None = None

    model_config = ConfigDict(from_attributes=True)

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., title="Название проекта", max_length=100)
    image: str = Field(..., title="Docker Image для деплоя", max_length=200)
    domain: str = Field(..., title="Домен для маршрутизации Traefik", max_length=255)

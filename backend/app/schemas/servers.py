import uuid

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress


class ServerBase(BaseModel):
    name: str = Field(..., title="Алиас сервера", max_length=100)
    ip_address: IPvAnyAddress = Field(..., title="IP адрес сервера")
    ssh_user: str = Field("root", title="Имя пользователя SSH")


class ServerCreate(ServerBase):
    initial_password: str | None = Field(
        None,
        title="Пароль для первоначальной настройки",
        description="Используется только один раз для добавления SSH-ключа. Не сохраняется в БД.",
    )


class ServerRead(ServerBase):
    id: uuid.UUID
    is_active: bool | None = None
    model_config = ConfigDict(from_attributes=True)


class ServerList(BaseModel):
    items: list[ServerRead]

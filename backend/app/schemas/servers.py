import uuid

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress


class ServerBase(BaseModel):
    name: str = Field(..., title="Алиас сервера", max_length=100)
    ip_address: IPvAnyAddress = Field(..., title="IP адрес сервера")
    ssh_user: str = Field("root", title="Имя пользователя SSH")


class ServerCreate(ServerBase):
    pass


class ServerRead(ServerBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


class ServerList(BaseModel):
    items: list[ServerRead]

"""Schemas de entrada/salida para el módulo de negocio (RF-02, RF-04)."""
from pydantic import BaseModel, Field


class NegocioCreate(BaseModel):
    nombre_negocio: str = Field(min_length=2, max_length=100)
    direccion: str | None = Field(default=None, max_length=200)
    telefono: str | None = Field(default=None, max_length=20)
    horario: str | None = Field(default=None, max_length=100)


class NegocioUpdate(BaseModel):
    """Todos los campos opcionales: se actualiza solo lo que venga en el body."""
    nombre_negocio: str | None = Field(default=None, min_length=2, max_length=100)
    direccion: str | None = Field(default=None, max_length=200)
    telefono: str | None = Field(default=None, max_length=20)
    horario: str | None = Field(default=None, max_length=100)


class NegocioResponse(BaseModel):
    id_negocio: int
    id_administrador: int
    nombre_negocio: str
    direccion: str | None
    telefono: str | None
    horario: str | None
    estado_bot: bool

    model_config = {"from_attributes": True}


class EstadoBotResponse(BaseModel):
    id_negocio: int
    estado_bot: bool

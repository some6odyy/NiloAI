"""Schemas de salida para el historial auditable de chats (RF-05)."""
from datetime import datetime
from pydantic import BaseModel


class MensajeResponse(BaseModel):
    id_mensaje: int
    emisor: str
    contenido: str
    fecha_hora: datetime
    tipo_mensaje: str

    model_config = {"from_attributes": True}


class ConversacionResponse(BaseModel):
    id_conversacion: int
    id_cliente: int
    nombre_cliente: str | None
    telefono_cliente: str
    fecha_inicio: datetime
    fecha_fin: datetime | None
    estado: str
    total_mensajes: int

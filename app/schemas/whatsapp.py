"""Schemas para RF-06: conectar el negocio a su número de WhatsApp Business."""
from pydantic import BaseModel, Field


class WhatsAppConexionUpdate(BaseModel):
    phone_number_id: str = Field(min_length=5, description="Phone Number ID de Meta (WhatsApp Business Cloud API)")
    access_token: str = Field(min_length=10, description="Token de acceso temporal o permanente de Meta")


class WhatsAppEstadoResponse(BaseModel):
    conectado: bool
    phone_number_id: str | None = None
    # El access_token NUNCA se devuelve una vez guardado.

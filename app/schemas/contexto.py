"""Schemas de entrada/salida para el módulo de contexto de IA (RF-03)."""
from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field

# Lista cerrada de modelos vigentes por proveedor (agosto 2026). Mantenerla
# acotada evita que el Dashboard guarde un identificador inválido que
# rompería las llamadas reales a la API en ai_service.py.
MODELOS_GEMINI = ("gemini-3.1-pro", "gemini-3.6-flash", "gemini-3.5-flash-lite")
MODELOS_OPENAI = ("gpt-5.5", "gpt-5.4-mini", "gpt-4o")
ModeloIA = Literal[
    "gemini-3.1-pro", "gemini-3.6-flash", "gemini-3.5-flash-lite",
    "gpt-5.5", "gpt-5.4-mini", "gpt-4o",
]


class ServicioCreate(BaseModel):
    nombre_servicio: str = Field(min_length=2, max_length=100)
    descripcion: str | None = None
    precio: Decimal = Field(gt=0, description="Precio en CLP")
    duracion_estimada: int = Field(gt=0, description="Minutos")


class ServicioUpdate(BaseModel):
    nombre_servicio: str | None = Field(default=None, min_length=2, max_length=100)
    descripcion: str | None = None
    precio: Decimal | None = Field(default=None, gt=0)
    duracion_estimada: int | None = Field(default=None, gt=0)


class ServicioResponse(BaseModel):
    id_servicio: int
    id_negocio: int
    nombre_servicio: str
    descripcion: str | None
    precio: Decimal
    duracion_estimada: int | None

    model_config = {"from_attributes": True}


class ContextoIAUpdate(BaseModel):
    reglas_negocio: str | None = Field(
        default=None,
        description="Ej: 'No se agenda fuera del horario de atención', 'Máximo 1 cita por cliente por día'",
    )
    instrucciones: str | None = Field(
        default=None,
        description="Ej: 'Responde de forma breve y amable, usa el nombre del cliente si lo conoces'",
    )
    consultar_catalogo: bool | None = Field(
        default=None, description="Si está apagado, el bot no incluye precios/servicios en sus respuestas",
    )
    agendar_automatico: bool | None = Field(
        default=None, description="Reservado: agendamiento autónomo por la IA (aún no implementado en el webhook)",
    )
    ai_provider: Literal["gemini", "openai"] | None = None
    ai_model: ModeloIA | None = None

    def model_post_init(self, __context) -> None:
        # Validación cruzada: que el modelo elegido realmente pertenezca
        # al proveedor elegido (evita guardar ai_provider=openai con
        # ai_model=gemini-3.6-flash, que rompería la llamada real).
        if self.ai_provider and self.ai_model:
            permitidos = MODELOS_GEMINI if self.ai_provider == "gemini" else MODELOS_OPENAI
            if self.ai_model not in permitidos:
                raise ValueError(f"El modelo '{self.ai_model}' no pertenece al proveedor '{self.ai_provider}'")


class ContextoIAResponse(BaseModel):
    id_contexto: int
    id_negocio: int
    reglas_negocio: str | None
    instrucciones: str | None
    consultar_catalogo: bool
    agendar_automatico: bool
    ai_provider: str
    ai_model: str
    fecha_actualizacion: datetime
    servicios: list[ServicioResponse] = []

    model_config = {"from_attributes": True}

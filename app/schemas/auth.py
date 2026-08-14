"""Schemas de entrada/salida para el módulo de autenticación (RF-01)."""
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class RegistroRequest(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    correo: EmailStr
    contrasena: str = Field(min_length=8, description="Mínimo 8 caracteres")


class LoginRequest(BaseModel):
    correo: EmailStr
    contrasena: str


class RecuperarContrasenaRequest(BaseModel):
    correo: EmailStr


class AdministradorResponse(BaseModel):
    id_administrador: int
    nombre: str
    correo: EmailStr
    fecha_registro: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

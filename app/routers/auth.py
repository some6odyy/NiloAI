"""RF-01 | Autenticación: registro, login y recuperación de contraseña."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import hashear_contrasena, verificar_contrasena, crear_access_token
from app.core.deps import obtener_administrador_actual
from app.models.administrador import Administrador
from app.schemas.auth import (
    RegistroRequest,
    LoginRequest,
    RecuperarContrasenaRequest,
    AdministradorResponse,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/registro", response_model=AdministradorResponse, status_code=status.HTTP_201_CREATED)
def registrar_administrador(datos: RegistroRequest, db: Session = Depends(get_db)):
    ya_existe = db.query(Administrador).filter(Administrador.correo == datos.correo).first()
    if ya_existe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una cuenta registrada con ese correo",
        )

    nuevo_administrador = Administrador(
        nombre=datos.nombre,
        correo=datos.correo,
        contrasena=hashear_contrasena(datos.contrasena),
    )
    db.add(nuevo_administrador)
    db.commit()
    db.refresh(nuevo_administrador)

    return nuevo_administrador


@router.post("/login", response_model=TokenResponse)
def iniciar_sesion(datos: LoginRequest, db: Session = Depends(get_db)):
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Correo o contraseña incorrectos",
    )

    administrador = db.query(Administrador).filter(Administrador.correo == datos.correo).first()
    if administrador is None:
        raise credenciales_invalidas

    if not verificar_contrasena(datos.contrasena, administrador.contrasena):
        raise credenciales_invalidas

    token = crear_access_token(administrador.id_administrador, administrador.correo)
    return TokenResponse(access_token=token)


@router.post("/recuperar-contrasena")
def recuperar_contrasena(datos: RecuperarContrasenaRequest, db: Session = Depends(get_db)):
    administrador = db.query(Administrador).filter(Administrador.correo == datos.correo).first()

    # Respuesta idéntica exista o no la cuenta: evita que alguien use este
    # endpoint para averiguar qué correos están registrados.
    if administrador:
        # TODO: generar un token temporal de un solo uso (ej. con expiración
        # de 15-30 min) y enviarlo por correo con un link a un formulario de
        # "nueva contraseña" en el Dashboard.
        pass

    return {"mensaje": "Si el correo está registrado, recibirás instrucciones para recuperar tu contraseña"}


@router.get("/yo", response_model=AdministradorResponse)
def obtener_perfil_propio(administrador_actual: Administrador = Depends(obtener_administrador_actual)):
    """Endpoint de ejemplo para probar que el token funciona: devuelve los
    datos del administrador dueño del token enviado."""
    return administrador_actual

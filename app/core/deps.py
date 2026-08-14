"""Dependency de FastAPI: extrae y valida el JWT del header Authorization,
y devuelve el Administrador autenticado. Se usa como Depends() en cualquier
endpoint del Dashboard que deba estar protegido."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import decodificar_access_token
from app.models.administrador import Administrador
from app.models.negocio import Negocio

# tokenUrl solo se usa para que /docs muestre el botón "Authorize"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def obtener_administrador_actual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Administrador:
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar la sesión",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decodificar_access_token(token)
    if payload is None:
        raise credenciales_invalidas

    id_administrador = payload.get("sub")
    if id_administrador is None:
        raise credenciales_invalidas

    administrador = (
        db.query(Administrador)
        .filter(Administrador.id_administrador == int(id_administrador))
        .first()
    )
    if administrador is None:
        raise credenciales_invalidas

    return administrador


def obtener_negocio_propio(
    id_negocio: int,
    db: Session = Depends(get_db),
    administrador_actual: Administrador = Depends(obtener_administrador_actual),
) -> Negocio:
    """Busca el negocio y confirma que pertenece al administrador del token.
    Esta es la barrera que evita que un barbero vea o edite los datos de
    otro negocio (aislamiento multitenant, RNF-02)."""
    negocio = db.query(Negocio).filter(Negocio.id_negocio == id_negocio).first()

    if negocio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Negocio no encontrado")

    if negocio.id_administrador != administrador_actual.id_administrador:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a este negocio")

    return negocio

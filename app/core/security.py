"""
Utilidades de seguridad para RF-01.
- Hash de contraseñas con bcrypt (nunca se guarda la contraseña en texto plano).
- Emisión y validación de JWT para mantener la sesión del administrador.
"""
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt, JWTError

from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


def hashear_contrasena(contrasena_plana: str) -> str:
    """Convierte la contraseña en un hash irreversible antes de guardarla."""
    hash_bytes = bcrypt.hashpw(contrasena_plana.encode("utf-8"), bcrypt.gensalt())
    return hash_bytes.decode("utf-8")


def verificar_contrasena(contrasena_plana: str, contrasena_hasheada: str) -> bool:
    """Compara la contraseña ingresada en el login contra el hash guardado."""
    return bcrypt.checkpw(contrasena_plana.encode("utf-8"), contrasena_hasheada.encode("utf-8"))


def crear_access_token(id_administrador: int, correo: str) -> str:
    """Genera un JWT firmado que el frontend guardará y enviará en cada
    request al Dashboard (header Authorization: Bearer <token>)."""
    expira = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(id_administrador),
        "correo": correo,
        "exp": expira,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decodificar_access_token(token: str) -> dict | None:
    """Valida la firma y expiración del token. Devuelve el payload o None
    si el token es inválido/expiró."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

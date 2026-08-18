"""
Utilidades de seguridad para RF-01.
- Hash de contraseñas con bcrypt (nunca se guarda la contraseña en texto plano).
- Emisión y validación de JWT para mantener la sesión del administrador.
"""
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt, JWTError
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, ENCRYPTION_KEY

_fernet = Fernet(ENCRYPTION_KEY.encode())


def hashear_contrasena(contrasena_plana: str) -> str:
    """Convierte la contraseña en un hash irreversible antes de guardarla."""
    hash_bytes = bcrypt.hashpw(contrasena_plana.encode("utf-8"), bcrypt.gensalt())
    return hash_bytes.decode("utf-8")


def verificar_contrasena(contrasena_plana: str, contrasena_hasheada: str) -> bool:
    """Compara la contraseña ingresada en el login contra el hash guardado.

    bcrypt 5.x lanza ValueError si la contraseña supera los 72 bytes (antes
    la truncaba en silencio). En login no controlamos qué escribe el
    cliente, así que lo capturamos: una contraseña demasiado larga
    simplemente no coincide, no debe tumbar el endpoint."""
    try:
        return bcrypt.checkpw(contrasena_plana.encode("utf-8"), contrasena_hasheada.encode("utf-8"))
    except ValueError:
        return False


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


def cifrar_texto(texto_plano: str) -> str:
    """Cifra credenciales sensibles antes de guardarlas en la BD — hoy se
    usa para el token de WhatsApp de cada negocio (RF-06). El cifrado es
    reversible (a diferencia del hash de contraseñas) porque necesitamos
    volver a leer el token real para llamar a la API de Meta."""
    return _fernet.encrypt(texto_plano.encode("utf-8")).decode("utf-8")


def descifrar_texto(texto_cifrado: str | None) -> str | None:
    """Descifra un valor guardado con cifrar_texto(). Devuelve None si no
    hay valor o si el cifrado es inválido (ej. se cambió ENCRYPTION_KEY)."""
    if not texto_cifrado:
        return None
    try:
        return _fernet.decrypt(texto_cifrado.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return None

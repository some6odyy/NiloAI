"""RF-05 | Historial auditable: el administrador revisa qué habló el bot
con cada cliente. Fundamental para detectar respuestas erróneas de la IA."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import obtener_negocio_propio
from app.models.negocio import Negocio
from app.models.conversacion import Conversacion, Mensaje
from app.models.cliente import Cliente
from app.schemas.conversacion import ConversacionResponse, MensajeResponse

router = APIRouter(prefix="/negocio/{id_negocio}/conversaciones", tags=["Historial"])


@router.get("", response_model=list[ConversacionResponse])
def listar_conversaciones(
    db: Session = Depends(get_db),
    negocio: Negocio = Depends(obtener_negocio_propio),
):
    """Lista todas las conversaciones del negocio, más recientes primero,
    con la cantidad de mensajes de cada una."""
    resultados = (
        db.query(Conversacion, Cliente, func.count(Mensaje.id_mensaje))
        .join(Cliente, Conversacion.id_cliente == Cliente.id_cliente)
        .outerjoin(Mensaje, Mensaje.id_conversacion == Conversacion.id_conversacion)
        .filter(Conversacion.id_negocio == negocio.id_negocio)
        .group_by(Conversacion.id_conversacion, Cliente.id_cliente)
        .order_by(Conversacion.fecha_inicio.desc())
        .all()
    )

    return [
        ConversacionResponse(
            id_conversacion=conversacion.id_conversacion,
            id_cliente=cliente.id_cliente,
            nombre_cliente=cliente.nombre_cliente,
            telefono_cliente=cliente.telefono,
            fecha_inicio=conversacion.fecha_inicio,
            fecha_fin=conversacion.fecha_fin,
            estado=conversacion.estado,
            total_mensajes=total_mensajes,
        )
        for conversacion, cliente, total_mensajes in resultados
    ]


@router.get("/{id_conversacion}/mensajes", response_model=list[MensajeResponse])
def listar_mensajes(
    id_conversacion: int,
    db: Session = Depends(get_db),
    negocio: Negocio = Depends(obtener_negocio_propio),
):
    """Devuelve el detalle mensaje por mensaje de una conversación puntual."""
    conversacion = (
        db.query(Conversacion)
        .filter(
            Conversacion.id_conversacion == id_conversacion,
            Conversacion.id_negocio == negocio.id_negocio,
        )
        .first()
    )
    if conversacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversación no encontrada")

    return (
        db.query(Mensaje)
        .filter(Mensaje.id_conversacion == id_conversacion)
        .order_by(Mensaje.fecha_hora)
        .all()
    )

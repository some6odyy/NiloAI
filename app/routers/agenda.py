"""Agenda: citas creadas por la IA (RF-07/08) o manualmente desde el Dashboard."""
from datetime import date as date_type
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import obtener_negocio_propio
from app.models.negocio import Negocio
from app.models.agenda import Agenda
from app.models.servicio import Servicio
from app.models.cliente import Cliente
from app.services.cliente_service import obtener_o_crear_cliente
from app.schemas.agenda import CitaCreate, CitaEstadoUpdate, CitaResponse

router = APIRouter(prefix="/negocio/{id_negocio}/agenda", tags=["Agenda"])


def _a_response(cita: Agenda, cliente: Cliente, servicio: Servicio) -> CitaResponse:
    return CitaResponse(
        id_agenda=cita.id_agenda,
        id_cliente=cliente.id_cliente,
        nombre_cliente=cliente.nombre_cliente,
        telefono_cliente=cliente.telefono,
        id_servicio=servicio.id_servicio,
        nombre_servicio=servicio.nombre_servicio,
        fecha_cita=cita.fecha_cita,
        hora_cita=cita.hora_cita,
        estado_cita=cita.estado_cita,
    )


@router.get("", response_model=list[CitaResponse])
def listar_citas(
    fecha: date_type | None = Query(default=None, description="Filtrar por fecha exacta (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    negocio: Negocio = Depends(obtener_negocio_propio),
):
    query = (
        db.query(Agenda, Cliente, Servicio)
        .join(Servicio, Agenda.id_servicio == Servicio.id_servicio)
        .join(Cliente, Agenda.id_cliente == Cliente.id_cliente)
        .filter(Servicio.id_negocio == negocio.id_negocio)
    )
    if fecha is not None:
        query = query.filter(Agenda.fecha_cita == fecha)

    resultados = query.order_by(Agenda.fecha_cita, Agenda.hora_cita).all()
    return [_a_response(cita, cliente, servicio) for cita, cliente, servicio in resultados]


@router.post("", response_model=CitaResponse, status_code=status.HTTP_201_CREATED)
def crear_cita(
    datos: CitaCreate,
    db: Session = Depends(get_db),
    negocio: Negocio = Depends(obtener_negocio_propio),
):
    servicio = (
        db.query(Servicio)
        .filter(Servicio.id_servicio == datos.id_servicio, Servicio.id_negocio == negocio.id_negocio)
        .first()
    )
    if servicio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ese servicio no existe en este negocio")

    cliente = obtener_o_crear_cliente(db, datos.telefono_cliente, datos.nombre_cliente)

    nueva_cita = Agenda(
        id_cliente=cliente.id_cliente,
        id_servicio=servicio.id_servicio,
        fecha_cita=datos.fecha_cita,
        hora_cita=datos.hora_cita,
        estado_cita="pendiente",
    )
    db.add(nueva_cita)
    db.commit()
    db.refresh(nueva_cita)

    return _a_response(nueva_cita, cliente, servicio)


def _obtener_cita_propia(id_agenda: int, db: Session, negocio: Negocio) -> tuple[Agenda, Cliente, Servicio]:
    resultado = (
        db.query(Agenda, Cliente, Servicio)
        .join(Servicio, Agenda.id_servicio == Servicio.id_servicio)
        .join(Cliente, Agenda.id_cliente == Cliente.id_cliente)
        .filter(Agenda.id_agenda == id_agenda, Servicio.id_negocio == negocio.id_negocio)
        .first()
    )
    if resultado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada")
    return resultado


@router.patch("/{id_agenda}/estado", response_model=CitaResponse)
def actualizar_estado_cita(
    id_agenda: int,
    datos: CitaEstadoUpdate,
    db: Session = Depends(get_db),
    negocio: Negocio = Depends(obtener_negocio_propio),
):
    cita, cliente, servicio = _obtener_cita_propia(id_agenda, db, negocio)
    cita.estado_cita = datos.estado_cita
    db.commit()
    db.refresh(cita)
    return _a_response(cita, cliente, servicio)


@router.delete("/{id_agenda}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_cita(
    id_agenda: int,
    db: Session = Depends(get_db),
    negocio: Negocio = Depends(obtener_negocio_propio),
):
    cita, _, _ = _obtener_cita_propia(id_agenda, db, negocio)
    db.delete(cita)
    db.commit()

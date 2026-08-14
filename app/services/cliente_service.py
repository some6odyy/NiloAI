"""
El Cliente se identifica por su número de WhatsApp. Tanto la agenda manual
(el administrador crea una cita a mano) como el webhook de WhatsApp (RF-06)
necesitan la misma lógica: si el teléfono ya existe, se reutiliza; si no,
se crea.
"""
from sqlalchemy.orm import Session

from app.models.cliente import Cliente


def obtener_o_crear_cliente(db: Session, telefono: str, nombre: str | None = None) -> Cliente:
    cliente = db.query(Cliente).filter(Cliente.telefono == telefono).first()

    if cliente is None:
        cliente = Cliente(telefono=telefono, nombre_cliente=nombre)
        db.add(cliente)
        db.commit()
        db.refresh(cliente)
    elif nombre and not cliente.nombre_cliente:
        # Si antes no teníamos su nombre y ahora sí, lo completamos.
        cliente.nombre_cliente = nombre
        db.commit()
        db.refresh(cliente)

    return cliente

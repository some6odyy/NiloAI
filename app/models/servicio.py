from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class Servicio(Base):
    """Catálogo de servicios de un negocio (ej. corte, perfilado de barba).
    Parte del contexto que se inyecta a la IA (RF-03)."""

    __tablename__ = "servicio"

    id_servicio = Column(Integer, primary_key=True, index=True)
    id_negocio = Column(Integer, ForeignKey("negocio.id_negocio"), nullable=False)
    nombre_servicio = Column(String(100), nullable=False)
    descripcion = Column(Text)
    precio = Column(Numeric(10, 2), nullable=False)
    duracion_estimada = Column(Integer)  # minutos

    negocio = relationship("Negocio", back_populates="servicios")

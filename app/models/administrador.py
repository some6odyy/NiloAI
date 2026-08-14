from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Administrador(Base):
    """Dueño/barbero que administra su negocio en el Dashboard (RF-01, RF-02)."""

    __tablename__ = "administrador"

    id_administrador = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(100), unique=True, nullable=False, index=True)
    contrasena = Column("contraseña", String(255), nullable=False)
    fecha_registro = Column(DateTime, server_default=func.now())

    negocios = relationship("Negocio", back_populates="administrador")

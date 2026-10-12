"""Modelos ORM de SQLAlchemy: tablas del sistema y sus relaciones."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarativa de todos los modelos del sistema."""


class Genero(Base):
    """Categoría literaria a la que pertenece un libro."""

    __tablename__ = "genero"

    id: Mapped[int] = mapped_column(primary_key=True)
    genero: Mapped[str] = mapped_column(String(50), unique=True)

    libros: Mapped[list[Libro]] = relationship(back_populates="genero")


class Editorial(Base):
    """Proveedor o distribuidora que provee los libros."""

    __tablename__ = "editorial"

    id: Mapped[int] = mapped_column(primary_key=True)
    proveedor: Mapped[str] = mapped_column(String(100), unique=True)
    pais: Mapped[str] = mapped_column(String(100))
    provincia: Mapped[str] = mapped_column(String(100))
    localidad: Mapped[str] = mapped_column(String(100))
    domicilio: Mapped[str] = mapped_column(String(200))
    telefono: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100))
    responsable: Mapped[str] = mapped_column(String(100))

    libros: Mapped[list[Libro]] = relationship(back_populates="editorial")


class Libro(Base):
    """Título del catálogo de la librería."""

    __tablename__ = "libro"

    id: Mapped[int] = mapped_column(primary_key=True)
    isbn: Mapped[str] = mapped_column(String(17), unique=True)
    titulo: Mapped[str] = mapped_column(String(200))
    autor: Mapped[str] = mapped_column(String(100))
    editorial_id: Mapped[int] = mapped_column(ForeignKey("editorial.id"))
    genero_id: Mapped[int] = mapped_column(ForeignKey("genero.id"))

    editorial: Mapped[Editorial] = relationship(back_populates="libros")
    genero: Mapped[Genero] = relationship(back_populates="libros")
    stock: Mapped[Stock | None] = relationship(back_populates="libro", uselist=False)
    precios: Mapped[list[Precio]] = relationship(back_populates="libro")


class Moneda(Base):
    """Moneda en la que se expresa un precio (ARS, USD, etc.)."""

    __tablename__ = "moneda"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(3), unique=True)
    nombre: Mapped[str] = mapped_column(String(100))

    precios: Mapped[list[Precio]] = relationship(back_populates="moneda")


class Stock(Base):
    """Cantidad disponible de un libro."""

    __tablename__ = "stock"

    id: Mapped[int] = mapped_column(primary_key=True)
    libro_id: Mapped[int] = mapped_column(ForeignKey("libro.id"), unique=True)
    existencia: Mapped[int] = mapped_column(default=0)

    libro: Mapped[Libro] = relationship(back_populates="stock")


class Precio(Base):
    """Valor de un libro expresado en una moneda determinada."""

    __tablename__ = "precio"

    id: Mapped[int] = mapped_column(primary_key=True)
    libro_id: Mapped[int] = mapped_column(ForeignKey("libro.id"))
    moneda_id: Mapped[int] = mapped_column(ForeignKey("moneda.id"))
    valor: Mapped[float] = mapped_column(Float)

    libro: Mapped[Libro] = relationship(back_populates="precios")
    moneda: Mapped[Moneda] = relationship(back_populates="precios")


class TipoCotizacion(Base):
    """Tipo de cotización del dólar (Blue, MEP, Oficial, etc.)."""

    __tablename__ = "tipo_cotizacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(50), unique=True)

    cotizaciones: Mapped[list[CotizacionDolar]] = relationship(
        back_populates="tipo_cotizacion"
    )


class CotizacionDolar(Base):
    """Registro histórico del valor del dólar para un tipo y una fecha."""

    __tablename__ = "cotizacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo_cotizacion_id: Mapped[int] = mapped_column(
        ForeignKey("tipo_cotizacion.id")
    )
    fecha: Mapped[date] = mapped_column(Date)
    valor_pesos: Mapped[float] = mapped_column(Float)

    tipo_cotizacion: Mapped[TipoCotizacion] = relationship(
        back_populates="cotizaciones"
    )

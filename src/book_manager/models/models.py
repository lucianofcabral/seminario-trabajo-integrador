"""Modelos ORM de SQLAlchemy: tablas del sistema y sus relaciones."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Montos exactos en la base (sin error de redondeo binario); en Python se leen
# como float porque las entidades trabajan con float.
Monto = Numeric(12, 2, asdecimal=False)


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
    # Al borrar un libro, el ORM borra su stock y sus precios en la misma
    # transacción.
    stock: Mapped[Stock | None] = relationship(
        back_populates="libro", uselist=False, cascade="all, delete-orphan"
    )
    precios: Mapped[list[Precio]] = relationship(
        back_populates="libro", cascade="all, delete-orphan"
    )


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
    __table_args__ = (UniqueConstraint("libro_id", "moneda_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    libro_id: Mapped[int] = mapped_column(ForeignKey("libro.id"))
    moneda_id: Mapped[int] = mapped_column(ForeignKey("moneda.id"))
    valor: Mapped[float] = mapped_column(Monto)

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
    __table_args__ = (UniqueConstraint("tipo_cotizacion_id", "fecha"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo_cotizacion_id: Mapped[int] = mapped_column(ForeignKey("tipo_cotizacion.id"))
    fecha: Mapped[date] = mapped_column(Date)
    valor_compra: Mapped[float] = mapped_column(Monto)
    valor_venta: Mapped[float] = mapped_column(Monto)

    tipo_cotizacion: Mapped[TipoCotizacion] = relationship(
        back_populates="cotizaciones"
    )


class PrecioWeb(Base):
    """Precio y datos de un libro obtenidos del sitio de Cúspide (scraping).

    Cada ejecución del scraper agrega un registro nuevo con su fecha de
    extracción, de modo que queda un histórico de precios web por libro.
    """

    __tablename__ = "precio_web"

    id: Mapped[int] = mapped_column(primary_key=True)
    libro_id: Mapped[int] = mapped_column(ForeignKey("libro.id"))
    titulo: Mapped[str] = mapped_column(String(200))
    autor: Mapped[str | None] = mapped_column(String(100))
    precio: Mapped[float] = mapped_column(Monto)
    url_imagen: Mapped[str] = mapped_column(String(500))
    formas_pago: Mapped[str] = mapped_column(String(500))
    descripcion: Mapped[str] = mapped_column(String(5000))
    url: Mapped[str] = mapped_column(String(500))
    fecha_extraccion: Mapped[date] = mapped_column(Date)

    libro: Mapped[Libro] = relationship()


class Auditoria(Base):
    """Registro de auditoría de las operaciones del sistema (Sprint 3, Ej 06).

    Cada operación auditada deja una entrada con la acción ejecutada, la fecha
    y un resumen de los detalles. El historial se consulta desde el menú.
    """

    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    accion: Mapped[str] = mapped_column(String(200))
    fecha: Mapped[date] = mapped_column(Date)
    detalles: Mapped[str] = mapped_column(String(1000))

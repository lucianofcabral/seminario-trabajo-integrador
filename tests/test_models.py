"""Tests de los modelos ORM (tablas y relaciones)."""

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from book_manager.models.models import (
    Base,
    CotizacionDolar,
    Editorial,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)

TABLAS = {
    "libro",
    "genero",
    "editorial",
    "moneda",
    "stock",
    "precio",
    "tipo_cotizacion",
    "cotizacion",
}


def test_tablas_creadas(tmp_path):
    """Crea las ocho tablas del sistema con sus nombres."""
    engine = create_engine(f"sqlite:///{tmp_path / 'm.db'}")
    Base.metadata.create_all(engine)

    assert TABLAS <= set(Base.metadata.tables)


def test_relaciones_entre_modelos(tmp_path):
    """Las relaciones resuelven: libro.editorial, .genero, .stock y .precios."""
    engine = create_engine(f"sqlite:///{tmp_path / 'm.db'}")
    Base.metadata.create_all(engine)

    genero = Genero(genero="Ficción")
    editorial = Editorial(
        proveedor="Editorial Alba",
        pais="Argentina",
        provincia="Buenos Aires",
        localidad="CABA",
        domicilio="Av. Siempre Viva 123",
        telefono="1145678901",
        email="contacto@editorialalba.com",
        responsable="Juan Pérez",
    )
    libro = Libro(
        isbn="9780306406157",
        titulo="El eco del silencio",
        autor="Marina Solís",
        editorial=editorial,
        genero=genero,
    )
    stock = Stock(libro=libro, existencia=10)
    moneda = Moneda(codigo="USD", nombre="dólar estadounidense")
    precio = Precio(libro=libro, moneda=moneda, valor=68.45)

    with Session(engine) as sesion:
        sesion.add_all([libro, stock, precio])
        sesion.commit()

    with Session(engine) as sesion:
        libro_db = sesion.scalar(select(Libro))
        assert libro_db.editorial.proveedor == "Editorial Alba"
        assert libro_db.genero.genero == "Ficción"
        assert libro_db.stock.existencia == 10
        assert libro_db.precios[0].valor == 68.45
        assert libro_db.precios[0].moneda.codigo == "USD"

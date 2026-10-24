"""Tests de los modelos ORM (tablas y relaciones)."""

from datetime import date

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import IntegrityError
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


def _libro_con_precio(sesion: Session) -> tuple[Libro, Moneda]:
    """Crea un libro con stock y un precio en USD para los tests."""
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
        genero=Genero(genero="Ficción"),
    )
    moneda = Moneda(codigo="USD", nombre="dólar estadounidense")
    sesion.add_all([libro, Stock(libro=libro, existencia=3)])
    sesion.add(Precio(libro=libro, moneda=moneda, valor=10))
    sesion.commit()
    return libro, moneda


def test_precio_unico_por_libro_y_moneda(tmp_path):
    """La base rechaza dos precios del mismo libro en la misma moneda."""
    engine = create_engine(f"sqlite:///{tmp_path / 'm.db'}")
    Base.metadata.create_all(engine)

    with Session(engine) as sesion:
        libro, moneda = _libro_con_precio(sesion)
        sesion.add(Precio(libro=libro, moneda=moneda, valor=20))
        with pytest.raises(IntegrityError):
            sesion.commit()


def test_cotizacion_unica_por_tipo_y_fecha(tmp_path):
    """La base rechaza dos cotizaciones del mismo tipo en la misma fecha."""
    engine = create_engine(f"sqlite:///{tmp_path / 'm.db'}")
    Base.metadata.create_all(engine)

    with Session(engine) as sesion:
        tipo = TipoCotizacion(tipo="Oficial")
        sesion.add(
            CotizacionDolar(
                tipo_cotizacion=tipo,
                fecha=date(2026, 10, 13),
                valor_compra=1530.0,
                valor_venta=1535.0,
            )
        )
        sesion.add(
            CotizacionDolar(
                tipo_cotizacion=tipo,
                fecha=date(2026, 10, 13),
                valor_compra=1535.0,
                valor_venta=1540.0,
            )
        )
        with pytest.raises(IntegrityError):
            sesion.commit()


def test_borrar_libro_borra_stock_y_precios(tmp_path):
    """Al borrar un libro se borran su stock y sus precios en la misma transacción."""
    engine = create_engine(f"sqlite:///{tmp_path / 'm.db'}")
    Base.metadata.create_all(engine)

    with Session(engine) as sesion:
        libro, _ = _libro_con_precio(sesion)
        sesion.delete(libro)
        sesion.commit()

        assert sesion.scalar(select(func.count()).select_from(Stock)) == 0
        assert sesion.scalar(select(func.count()).select_from(Precio)) == 0

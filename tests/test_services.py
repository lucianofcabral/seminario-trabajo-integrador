"""Tests de las reglas de negocio de la capa de servicios."""

from datetime import date

import pytest

from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)
from book_manager.repositories import repositories as repos
from book_manager.services.services import (
    ServicioCotizacionDolar,
    ServicioEditorial,
    ServicioGenero,
    ServicioLibro,
    ServicioMoneda,
    ServicioPrecio,
    ServicioStock,
    ServicioTipoCotizacion,
)

ARCHIVOS = {
    repos.RepoLibroCSV: "libro.csv",
    repos.RepoGeneroCSV: "genero.csv",
    repos.RepoEditorialCSV: "editorial.csv",
    repos.RepoMonedaCSV: "moneda.csv",
    repos.RepoStockCSV: "stock.csv",
    repos.RepoPrecioCSV: "precio.csv",
    repos.RepoTipoCotizacionCSV: "tipo_cotizacion.csv",
    repos.RepoCotizacionDolarCSV: "cotizacion.csv",
}


@pytest.fixture(autouse=True)
def csv_temporales(monkeypatch, tmp_path):
    """Redirige todos los repositorios CSV a archivos vacíos temporales."""
    for repo_cls, nombre in ARCHIVOS.items():
        monkeypatch.setattr(repo_cls, "ruta", tmp_path / nombre)


@pytest.fixture
def libro() -> Libro:
    """Crea una editorial, un género y un libro que los referencia."""
    editorial = ServicioEditorial().crear(
        Editorial(
            proveedor="Editorial Alba",
            pais="Argentina",
            provincia="Buenos Aires",
            localidad="CABA",
            domicilio="Av. Siempre Viva 123",
            telefono="1145678901",
            email="contacto@alba.com",
            responsable="Juan Pérez",
        )
    )
    genero = ServicioGenero().crear(Genero(genero="Ficción"))
    return ServicioLibro().crear(
        Libro(
            isbn="9780306406157",
            titulo="El eco del silencio",
            autor="Marina Solís",
            editorial_id=editorial.id,
            genero_id=genero.id,
        )
    )


def test_libro_con_editorial_inexistente_se_rechaza(libro):
    with pytest.raises(ValueError, match="editorial"):
        ServicioLibro().crear(
            libro.model_copy(update={"isbn": "9781234567897", "editorial_id": 99})
        )


def test_relaciones_del_libro(libro):
    servicio = ServicioLibro()
    assert servicio.editorial_de(libro).proveedor == "Editorial Alba"
    assert servicio.genero_de(libro).genero == "Ficción"
    assert ServicioGenero().libros_de(libro.genero_id) == [libro]
    assert ServicioEditorial().libros_de(libro.editorial_id) == [libro]


def test_no_se_borra_genero_con_libros(libro):
    with pytest.raises(ValueError, match="libro"):
        ServicioGenero().eliminar(libro.genero_id)
    assert ServicioGenero().leer_por_id(libro.genero_id) is not None


def test_no_se_borra_editorial_con_libros(libro):
    with pytest.raises(ValueError):
        ServicioEditorial().eliminar(libro.editorial_id)


def test_borrar_libro_borra_su_stock_y_precios(libro):
    moneda = ServicioMoneda().crear(Moneda(codigo="USD", nombre="dólar"))
    ServicioStock().crear(Stock(libro_id=libro.id, existencia=5))
    ServicioPrecio().crear(Precio(libro_id=libro.id, moneda_id=moneda.id, valor=10))

    assert ServicioLibro().eliminar(libro.id) is True

    assert ServicioStock().leer_todos() == []
    assert ServicioPrecio().leer_todos() == []
    # Sin precios, la moneda ya se puede borrar.
    assert ServicioMoneda().eliminar(moneda.id) is True


def test_no_se_borra_moneda_con_precios(libro):
    moneda = ServicioMoneda().crear(Moneda(codigo="USD", nombre="dólar"))
    ServicioPrecio().crear(Precio(libro_id=libro.id, moneda_id=moneda.id, valor=10))

    with pytest.raises(ValueError):
        ServicioMoneda().eliminar(moneda.id)


def test_eliminar_inexistente_devuelve_false():
    assert ServicioGenero().eliminar(99) is False


def test_stock_de_libro_inexistente_se_rechaza():
    with pytest.raises(ValueError, match="libro"):
        ServicioStock().crear(Stock(libro_id=99, existencia=1))


def test_modificar_stock(libro):
    ServicioStock().crear(Stock(libro_id=libro.id, existencia=100))

    ServicioStock().modificar_stock(libro.id, 55)

    assert ServicioLibro().stock_de(libro.id).existencia == 55


def test_modificar_precio(libro):
    moneda = ServicioMoneda().crear(Moneda(codigo="USD", nombre="dólar"))
    ServicioPrecio().crear(Precio(libro_id=libro.id, moneda_id=moneda.id, valor=68.45))

    ServicioPrecio().modificar_precio(libro.id, moneda.id, 99.99)

    assert ServicioLibro().precios_de(libro.id)[0].valor == 99.99


def test_modificar_stock_sin_registro_lanza_value_error(libro):
    with pytest.raises(ValueError):
        ServicioStock().modificar_stock(libro.id, 1)


def test_cotizaciones_por_tipo():
    tipo = ServicioTipoCotizacion().crear(TipoCotizacion(tipo="Blue"))
    servicio = ServicioCotizacionDolar()
    for dia, valor in [(2, 1500.0), (1, 1490.0)]:
        servicio.crear(
            CotizacionDolar(
                tipo_cotizacion_id=tipo.id, fecha=date(2026, 1, dia), valor_pesos=valor
            )
        )

    assert [c.valor_pesos for c in servicio.historico(tipo.id)] == [1490.0, 1500.0]
    assert servicio.ultima(tipo.id).valor_pesos == 1500.0
    assert servicio.cotizacion_del_dia(tipo.id, date(2026, 1, 1)).valor_pesos == 1490.0

    with pytest.raises(ValueError):
        ServicioTipoCotizacion().eliminar(tipo.id)


def test_cotizacion_de_tipo_inexistente_se_rechaza():
    with pytest.raises(ValueError, match="tipo de cotización"):
        ServicioCotizacionDolar().crear(
            CotizacionDolar(tipo_cotizacion_id=99, fecha=date(2026, 1, 1), valor_pesos=1)
        )

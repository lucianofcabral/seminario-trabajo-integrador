"""Tests de la consola (catálogo y resolución de referencias)."""

from book_manager.entities.entities import Editorial, Genero, Libro
from book_manager.ui import console
from book_manager.ui.console import _construir_tablas, _entidad_a_fila


def _armar_catalogo(conexion):
    tablas = _construir_tablas(conexion)
    console.CATALOGO.update({t.clave: t for t in tablas})
    return tablas


def test_construir_tablas(conexion):
    tablas = _armar_catalogo(conexion)
    assert len(tablas) == 8
    assert {t.clave for t in tablas} >= {"libro", "genero", "editorial", "moneda"}


def test_entidad_a_fila_resuelve_fk(conexion):
    tablas = _armar_catalogo(conexion)
    libro_tabla = next(t for t in tablas if t.clave == "libro")

    libro = Libro(
        isbn="9780306406157",
        titulo="El eco",
        autor="Marina",
        editorial=Editorial(
            proveedor="Alba",
            pais="Argentina",
            provincia="Buenos Aires",
            localidad="CABA",
            domicilio="Av 1",
            telefono="111",
            email="a@b.com",
            responsable="Juan",
        ),
        genero=Genero(genero="Ficción"),
    )

    fila = _entidad_a_fila(libro_tabla, libro)

    assert fila["isbn"] == "9780306406157"
    assert fila["editorial"] == "Alba"
    assert fila["genero"] == "Ficción"


def test_exportar_precios_csv(conexion_poblada, tmp_path, capsys):
    from book_manager.ui.console import _exportar_precios_csv

    ruta = tmp_path / "exports" / "precios.csv"
    _exportar_precios_csv(conexion_poblada, ruta)

    cabecera = ruta.read_text(encoding="utf-8").splitlines()[0]
    assert cabecera.startswith("isbn,titulo,moneda,valor,ARS ")
    assert "Exportado a" in capsys.readouterr().out


# --- Ej 07: nuevas opciones del menú ---


def test_ver_historial_auditoria_vacio(conexion_poblada, capsys):
    from book_manager.ui.console import _ver_historial_auditoria

    _ver_historial_auditoria(conexion_poblada)

    assert "No hay operaciones auditadas" in capsys.readouterr().out


def test_ver_historial_auditoria_muestra_entradas(conexion_poblada, capsys):
    from book_manager.entities.entities import Genero
    from book_manager.services import auditoria
    from book_manager.services.services import ServicioGenero
    from book_manager.ui.console import _ver_historial_auditoria

    auditoria.configurar_auditoria(conexion_poblada)
    try:
        ServicioGenero(conexion=conexion_poblada).crear(Genero(genero="Novela"))
        _ver_historial_auditoria(conexion_poblada)
    finally:
        auditoria._repo = None

    salida = capsys.readouterr().out
    assert "crear Genero" in salida
    assert "genero='Novela'" in salida


def test_generar_reporte_imprime_ruta(conexion_poblada, capsys, monkeypatch):
    from book_manager.ui import console
    from book_manager.ui.console import _generar_reporte

    class _ReporteFalso:
        def __init__(self, conexion=None):
            pass

        def generar_reporte(self):
            return ["a", "b"]

    monkeypatch.setattr(console, "ServicioReporte", _ReporteFalso)

    _generar_reporte(conexion_poblada)

    assert "Reporte generado en" in capsys.readouterr().out


def test_ejecutar_scraping_pide_umbral(conexion_poblada, capsys, monkeypatch):
    from book_manager.ui import console
    from book_manager.ui.console import _ejecutar_scraping

    llamadas = {}
    monkeypatch.setattr(
        console, "obtener_catalogo", lambda origen: [{"titulo": "X", "libro_id": 1}]
    )

    def _scraping_falso(catalogo, umbral=None, conexion=None):
        llamadas["umbral"] = umbral
        return ["alerta"]

    monkeypatch.setattr(console, "ejecutar_scraping", _scraping_falso)
    monkeypatch.setattr("builtins.input", lambda *_: "5000")

    _ejecutar_scraping(conexion_poblada)

    assert llamadas["umbral"] == 5000.0
    assert "Scraping terminado: 1 alerta(s)" in capsys.readouterr().out

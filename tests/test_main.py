"""Tests del punto de entrada."""

from book_manager.main import _base_vacia


def test_base_vacia_con_base_sin_datos(conexion):
    assert _base_vacia(conexion) is True


def test_base_vacia_con_base_poblada(conexion_poblada):
    assert _base_vacia(conexion_poblada) is False

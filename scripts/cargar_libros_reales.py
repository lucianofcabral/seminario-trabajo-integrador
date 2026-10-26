"""Carga libros reales (que existen en Cúspide) para probar el scraper del Sprint 3.

Los datos de ejemplo del TP1 tienen títulos inventados, así que el scraper no
encuentra nada en Cúspide. Este script agrega algunos libros reales al catálogo
para poder probar el flujo completo (scraping → alertas → reporte).

Es idempotente: si un ISBN ya está en la base, lo saltea.

Uso:
    uv run python scripts/cargar_libros_reales.py
"""

from __future__ import annotations

from book_manager.database.connection import ConexionDB
from book_manager.entities.entities import (
    Libro,
    Moneda,
    Precio,
    Stock,
)
from book_manager.services.services import (
    ServicioEditorial,
    ServicioGenero,
    ServicioLibro,
    ServicioPrecio,
    ServicioStock,
)

# (isbn, titulo, autor, género, precio en USD)
LIBROS_REALES = [
    (
        "9780307474728",
        "Cien años de soledad",
        "Gabriel García Márquez",
        "Ficción",
        18.99,
    ),
    ("9789871138524", "Rayuela", "Julio Cortázar", "Ficción", 22.50),
    ("9789871165894", "1984", "George Orwell", "Ciencia ficción", 15.00),
    ("9789878000974", "El Principito", "Antoine de Saint-Exupéry", "Ficción", 12.00),
    ("9789871144848", "El túnel", "Ernesto Sabato", "Ficción", 16.50),
    ("9789500398574", "Ficciones", "Jorge Luis Borges", "Ficción", 19.99),
    ("9788434440678", "El amanecer de todo", "David Graeber", "Ensayo", 66.01),
]


def main(conexion: ConexionDB | None = None) -> None:
    conexion = conexion or ConexionDB()
    servicio_editorial = ServicioEditorial(conexion=conexion)
    servicio_genero = ServicioGenero(conexion=conexion)
    servicio_libro = ServicioLibro(conexion=conexion)
    servicio_precio = ServicioPrecio(conexion=conexion)
    servicio_stock = ServicioStock(conexion=conexion)

    # Reusa una editorial existente y arma un mapa de géneros por nombre.
    editorial = servicio_editorial.leer_todos()[0]
    generos = {g.genero: g for g in servicio_genero.leer_todos()}

    existentes = {libro.isbn for libro in servicio_libro.leer_todos()}

    for isbn, titulo, autor, genero_nombre, precio_usd in LIBROS_REALES:
        if isbn in existentes:
            print(f"  (ya estaba) {titulo}")
            continue
        genero = generos[genero_nombre]
        libro = servicio_libro.crear(
            Libro(
                isbn=isbn,
                titulo=titulo,
                autor=autor,
                editorial=editorial,
                genero=genero,
            )
        )
        servicio_precio.crear(
            Precio(
                libro=libro,
                moneda=Moneda(codigo="USD", nombre="dólar estadounidense"),
                valor=precio_usd,
            )
        )
        servicio_stock.crear(Stock(libro=libro, existencia=10))
        print(f"  Cargado: {titulo} (${precio_usd:.2f} USD)")

    print("Listo. Ahora ejecutá el scraping y el reporte.")


if __name__ == "__main__":
    main()

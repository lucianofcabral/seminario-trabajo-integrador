"""Migración de datos: lee los CSV del TP1, genera .sql y puebla la base."""

import csv
from pathlib import Path

from sqlalchemy import Date, String, text

from book_manager.database.connection import ConexionDB
from book_manager.models.models import Base


def migrar_datos(carpeta_csvs: str, carpeta_sqls: str) -> None:
    """Lee los archivos CSV y crea un archivo `.sql` con los INSERT por tabla.

    Args:
        carpeta_csvs: Carpeta donde se encuentran los archivos CSV de origen.
        carpeta_sqls: Carpeta donde se deben guardar los archivos SQL generados.
    """
    destino = Path(carpeta_sqls)
    destino.mkdir(parents=True, exist_ok=True)

    for csv_path in sorted(Path(carpeta_csvs).glob("*.csv")):
        tabla = csv_path.stem
        columnas, filas = _leer_csv(csv_path)
        if not filas:
            continue
        sentencias = [_insert_sql(tabla, columnas, fila) for fila in filas]
        (destino / f"{tabla}.sql").write_text(
            "\n".join(sentencias) + "\n", encoding="utf-8"
        )


def poblar_base_de_datos(conexion: ConexionDB, carpeta_sqls: str) -> None:
    """Crea las tablas y ejecuta los `.sql` en orden de dependencias (FK)."""
    Base.metadata.create_all(conexion.engine)

    for tabla in Base.metadata.sorted_tables:
        sql_path = Path(carpeta_sqls) / f"{tabla.name}.sql"
        if not sql_path.exists():
            continue
        with conexion.transaccion() as sesion:
            for linea in sql_path.read_text(encoding="utf-8").splitlines():
                sentencia = linea.strip().rstrip(";")
                if sentencia:
                    sesion.execute(text(sentencia))

    _resetear_secuencias(conexion)


def _resetear_secuencias(conexion: ConexionDB) -> None:
    """Avanza las secuencias de id tras insertar valores explícitos (PostgreSQL).

    Como los CSV preservan sus `id`, la secuencia `SERIAL` queda en 1 y el
    siguiente INSERT autoincremental colisionaría. `setval` la lleva al máximo
    actual. En otros dialectos (p. ej. SQLite) no hay secuencia y no hace nada.
    """
    if conexion.engine.dialect.name != "postgresql":
        return
    for tabla in Base.metadata.sorted_tables:
        with conexion.transaccion() as sesion:
            sesion.execute(
                text(
                    f"SELECT setval(pg_get_serial_sequence('{tabla.name}', 'id'), "
                    f"(SELECT COALESCE(MAX(id), 1) FROM {tabla.name}))"
                )
            )


def _leer_csv(csv_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Lee un CSV y devuelve (columnas, filas) con los valores como texto."""
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        columnas = list(reader.fieldnames or [])
        filas = list(reader)
    return columnas, filas


def _insert_sql(tabla: str, columnas: list[str], fila: dict[str, str]) -> str:
    """Arma la sentencia INSERT de una fila."""
    valores = [_valor_sql(tabla, columna, fila[columna]) for columna in columnas]
    return (
        f"INSERT INTO {tabla} ({', '.join(columnas)}) "
        f"VALUES ({', '.join(valores)});"
    )


def _valor_sql(tabla: str, columna: str, valor: str) -> str:
    """Formatea un valor según el tipo de su columna en el modelo."""
    if valor == "":
        return "NULL"
    if _es_texto(tabla, columna):
        return "'" + valor.replace("'", "''") + "'"
    return valor


def _es_texto(tabla: str, columna: str) -> bool:
    """Indica si la columna es de texto o fecha (hay que entrecomillarla)."""
    tipo = Base.metadata.tables[tabla].columns[columna].type
    return isinstance(tipo, (String, Date))

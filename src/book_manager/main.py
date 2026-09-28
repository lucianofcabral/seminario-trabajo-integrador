from book_manager.preload_data.preload_data import precargar_datos
from book_manager.ui.console import main as console_main


def main(import_default_data: bool = True) -> None:
    """Ejecuta el sistema: precarga opcional de datos y menú de consola.

    Args:
        import_default_data: Si es True, regenera los CSV de ejemplo antes de
            abrir el menú (pisa lo cargado). Con False se usan los CSV que ya
            están en `migrations/csv`.
    """
    if import_default_data:
        precargar_datos(renovar=True)
    console_main()


if __name__ == "__main__":
    main()

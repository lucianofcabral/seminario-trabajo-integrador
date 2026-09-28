def main() -> None:
    """Punto de entrada del paquete (entry point `book-manager`)."""
    from book_manager.migrations.migrations import migrar_csvs
    from book_manager.ui.console import main as console_main

    migrar_csvs(renovar=True)
    console_main()

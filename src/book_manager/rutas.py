from pathlib import Path

ROOT: Path = Path(__file__).parent

CSV_FOLDER_PATH = ROOT / "migrations" / "csv"
SQL_FOLDER_PATH = ROOT / "migrations" / "sql"
EXPORTS_FOLDER_PATH = ROOT.parent.parent / "exports"

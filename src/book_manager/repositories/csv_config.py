import csv
from typing import Any

csv_config: dict[str, Any] = {
    "delimiter": ",",
    "quotechar": '"',
    "quoting": csv.QUOTE_NONNUMERIC,
}

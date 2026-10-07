"""Comprobaciones de formato compartidas por los extractores.

Si una fuente cambia el formato de un archivo, el extractor se detiene con
`SourceFormatError` en lugar de cargar datos mal interpretados.
"""

from __future__ import annotations

import gzip
import re
from datetime import datetime
from pathlib import Path

from metabo.errors import SourceFormatError


def read_first_line(path: Path) -> str:
    """Primera línea de un archivo de texto, descomprimiendo si termina en .gz."""
    opener = gzip.open if path.suffix == ".gz" else open
    try:
        with opener(path, "rt", encoding="utf-8") as handle:
            return handle.readline().rstrip("\r\n")
    except (OSError, UnicodeDecodeError) as exc:
        raise SourceFormatError(f"No se pudo leer {path.name}: {exc}") from exc


def check_header(path: Path, expected: tuple[str, ...]) -> None:
    """Comprueba que la primera línea del TSV tenga exactamente las columnas esperadas."""
    header = tuple(read_first_line(path).split("\t"))
    if header != expected:
        raise SourceFormatError(
            f"{path.name} cambió de formato: se esperaban las columnas {list(expected)} "
            f"y se encontraron {list(header)}. Revisa la documentación de la fuente antes de "
            "adaptar el extractor."
        )


def find_release(text: str, pattern: str, what: str) -> str:
    """Devuelve el primer grupo de `pattern` (multilínea) en `text` o falla con un mensaje."""
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        raise SourceFormatError(f"No se encontró la versión en {what}.")
    return match.group(1)


def english_date_to_iso(value: str, what: str) -> str:
    """Convierte '02-Sep-2026' a '2026-09-02' sin depender del idioma del sistema."""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    match = re.fullmatch(r"([0-9]{2})-([A-Z][a-z]{2})-([0-9]{4})", value)
    if not match or match.group(2) not in months:
        raise SourceFormatError(f"Fecha de versión no válida en {what}: {value!r}")
    day, month, year = int(match.group(1)), months.index(match.group(2)) + 1, int(match.group(3))
    try:
        return datetime(year, month, day).date().isoformat()
    except ValueError as exc:
        raise SourceFormatError(f"Fecha de versión no válida en {what}: {value!r}") from exc

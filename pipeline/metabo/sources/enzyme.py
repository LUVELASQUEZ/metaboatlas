"""Extractor de ENZYME (sección 3 de docs/MANUAL.md): nomenclatura EC oficial.

Descarga del FTP oficial de Expasy:

- `enzclass.txt`: clases, subclases y sub-subclases EC.
- `enzyme.dat`: cada número EC con su nombre aceptado, nombres alternativos y
  reacción catalizada (formato descrito en `enzuser.txt`).

Ambos archivos declaran su release ("Release: 02-Sep-2026" y "Release of
02-Sep-2026"); la versión es esa fecha en ISO (2026-09-02) y deben coincidir.
"""

from __future__ import annotations

import re
from pathlib import Path

from metabo.download import Downloader
from metabo.errors import SourceFormatError
from metabo.manifest import DownloadRecord
from metabo.sources.formats import english_date_to_iso, find_release

FUENTE = "enzyme"
BASE_URL = "https://ftp.expasy.org/databases/enzyme"
CLASS_URL = f"{BASE_URL}/enzclass.txt"
DAT_URL = f"{BASE_URL}/enzyme.dat"

_CLASS_RELEASE = r"^Release:\s+(\S+)\s*$"
_DAT_RELEASE = r"^CC\s+Release of (\S+)\s*$"
# Línea de clase de enzclass.txt, p. ej. "1. 1. 1.-    With NAD(+) or NADP(+) as acceptor."
_CLASS_LINE = re.compile(r"^[1-7]\.\s*(?:[0-9]+|-)\.\s*(?:[0-9]+|-)\.-\s+\S", re.MULTILINE)
_DAT_ENTRY = re.compile(
    r"^ID   [1-7]\.[0-9]+\.[0-9]+\.n?[0-9]+\n(?:[A-Z]{2}   .*\n)*?DE   ", re.MULTILINE
)


def class_release(text: str) -> str:
    """Versión (AAAA-MM-DD) declarada en enzclass.txt."""
    raw = find_release(text, _CLASS_RELEASE, "enzclass.txt")
    return english_date_to_iso(raw, "enzclass.txt")


def dat_release(text: str) -> str:
    """Versión (AAAA-MM-DD) declarada en la cabecera de enzyme.dat."""
    raw = find_release(text, _DAT_RELEASE, "enzyme.dat")
    return english_date_to_iso(raw, "enzyme.dat")


def check_class_file(text: str) -> None:
    if not _CLASS_LINE.search(text):
        raise SourceFormatError(
            "enzclass.txt cambió de formato: no tiene líneas de clase EC "
            "(p. ej. '1. 1. 1.-    With NAD(+) or NADP(+) as acceptor.')."
        )


def check_dat_file(text: str) -> None:
    if not _DAT_ENTRY.search(text):
        raise SourceFormatError(
            "enzyme.dat cambió de formato: no tiene entradas con líneas 'ID' y 'DE'. "
            "Revisa enzuser.txt antes de adaptar el extractor."
        )


def extract(downloader: Downloader, raw_dir: Path) -> tuple[str, list[DownloadRecord]]:
    """Descarga la versión vigente de ENZYME a raw/enzyme/<AAAA-MM-DD>/."""
    version = class_release(downloader.fetch_text(FUENTE, CLASS_URL))

    records = []
    for url, release_of, check in (
        (CLASS_URL, class_release, check_class_file),
        (DAT_URL, dat_release, check_dat_file),
    ):
        record = downloader.download(FUENTE, url, version)
        text = (raw_dir / record.archivo).read_text(encoding="utf-8")
        found = release_of(text)
        # Si Expasy publicó un release durante la descarga, las versiones no coinciden.
        if found != version:
            raise SourceFormatError(
                f"{Path(record.archivo).name} es del release {found}, pero se esperaba "
                f"{version}; vuelve a ejecutar la extracción."
            )
        check(text)
        records.append(record)
    return version, records

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
from dataclasses import dataclass
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


# ---------------------------------------------------------------------------
# Lectura de enzyme.dat para la curaduría
# ---------------------------------------------------------------------------

_TRANSFERRED = re.compile(r"^Transferred entry:\s*(.+?)\.?$")


@dataclass(frozen=True)
class EnzymeEntry:
    ec: str  # CURIE, p. ej. EC:2.7.1.1
    nombre: str
    eliminada: bool
    transferida_a: tuple[str, ...]  # CURIE de los EC que la reemplazan

    @property
    def vigente(self) -> bool:
        return not self.eliminada and not self.transferida_a


def _entry(ec: str, description: str) -> EnzymeEntry:
    transferred = _TRANSFERRED.match(description)
    targets: tuple[str, ...] = ()
    if transferred:
        targets = tuple(
            f"EC:{t}" for t in re.findall(r"[1-7]\.[0-9]+\.[0-9]+\.n?[0-9]+", transferred.group(1))
        )
    return EnzymeEntry(
        ec=f"EC:{ec}",
        nombre=description.removesuffix("."),
        eliminada=description.startswith("Deleted entry"),
        transferida_a=targets,
    )


def parse_entries(text: str) -> dict[str, EnzymeEntry]:
    """Entradas de enzyme.dat (líneas ID y DE, terminadas en '//'), indexadas por CURIE."""
    entries: dict[str, EnzymeEntry] = {}
    ec: str | None = None
    description: list[str] = []
    for line in text.splitlines():
        if line.startswith("ID   "):
            ec, description = line[5:].strip(), []
        elif line.startswith("DE   ") and ec is not None:
            description.append(line[5:].strip())
        elif line.startswith("//") and ec is not None:
            if not description:
                raise SourceFormatError(f"enzyme.dat: la entrada {ec} no tiene línea DE.")
            entry = _entry(ec, " ".join(description))
            entries[entry.ec] = entry
            ec = None
    return entries


def read_entries(path: Path) -> dict[str, EnzymeEntry]:
    return parse_entries(path.read_text(encoding="utf-8"))

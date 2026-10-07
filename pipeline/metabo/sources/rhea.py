"""Extractor de Rhea (sección 3 de docs/MANUAL.md): reacciones, direcciones y números EC.

Descarga del FTP oficial de Expasy, en la carpeta de la versión vigente:

- `rhea-release.properties`: número y fecha del release.
- `rhea-directions.tsv`: cada reacción maestra con sus tres direcciones (LR, RL, BI).
- `rhea2ec.tsv`: correspondencia entre reacciones y números EC.

Los participantes ChEBI de cada reacción no están en estos TSV (solo en el volcado
RDF y en SPARQL); se integran en una tarea posterior.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from metabo.download import Downloader
from metabo.errors import SourceFormatError
from metabo.manifest import DownloadRecord

FUENTE = "rhea"
BASE_URL = "https://ftp.expasy.org/databases/rhea"
RELEASE_URL = f"{BASE_URL}/rhea-release.properties"

# Archivo TSV -> encabezado esperado. Si Rhea cambia las columnas, el extractor se
# detiene en lugar de cargar datos mal interpretados.
TSV_FILES: dict[str, tuple[str, ...]] = {
    "rhea-directions.tsv": ("RHEA_ID_MASTER", "RHEA_ID_LR", "RHEA_ID_RL", "RHEA_ID_BI"),
    "rhea2ec.tsv": ("RHEA_ID", "DIRECTION", "MASTER_ID", "ID"),
}

_RELEASE_NUMBER = re.compile(r"^[0-9]+$")
_RELEASE_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


@dataclass(frozen=True)
class Release:
    numero: str
    fecha: str


def parse_release(text: str) -> Release:
    """Lee `rhea.release.number` y `rhea.release.date` de rhea-release.properties."""
    values: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "!")) or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    numero = values.get("rhea.release.number", "")
    fecha = values.get("rhea.release.date", "")
    if not _RELEASE_NUMBER.match(numero):
        raise SourceFormatError(
            f"rhea-release.properties no tiene un rhea.release.number válido: {numero!r}"
        )
    if not _RELEASE_DATE.match(fecha):
        raise SourceFormatError(
            f"rhea-release.properties no tiene un rhea.release.date válido: {fecha!r}"
        )
    return Release(numero=numero, fecha=fecha)


def check_header(path: Path, expected: tuple[str, ...]) -> None:
    """Comprueba que la primera línea del TSV tenga exactamente las columnas esperadas."""
    with path.open(encoding="utf-8") as handle:
        header = tuple(handle.readline().rstrip("\r\n").split("\t"))
    if header != expected:
        raise SourceFormatError(
            f"{path.name} cambió de formato: se esperaban las columnas {list(expected)} "
            f"y se encontraron {list(header)}. Revisa el README del FTP de Rhea antes de "
            "adaptar el extractor."
        )


def extract(downloader: Downloader, raw_dir: Path) -> tuple[Release, list[DownloadRecord]]:
    """Descarga la versión vigente de Rhea a raw/rhea/<release>/ y devuelve sus registros."""
    release = parse_release(downloader.fetch_text(FUENTE, RELEASE_URL))

    records = [downloader.download(FUENTE, RELEASE_URL, release.numero)]
    for filename, expected in TSV_FILES.items():
        record = downloader.download(FUENTE, f"{BASE_URL}/tsv/{filename}", release.numero)
        check_header(raw_dir / record.archivo, expected)
        records.append(record)

    # Si Rhea publicó un release durante la descarga, los archivos podrían mezclar
    # versiones bajo la misma carpeta: se detiene en lugar de registrarlos.
    final = parse_release(downloader.fetch_text(FUENTE, RELEASE_URL))
    if final != release:
        raise SourceFormatError(
            f"Rhea cambió de release durante la descarga ({release.numero} -> {final.numero}); "
            "vuelve a ejecutar la extracción."
        )
    return release, records

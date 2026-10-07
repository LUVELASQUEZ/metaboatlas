"""Extractor de Rhea (sección 3 de docs/MANUAL.md): reacciones, direcciones y números EC.

Descarga del FTP oficial de Expasy, en la carpeta de la versión vigente:

- `rhea-release.properties`: número y fecha del release.
- `rhea-directions.tsv`: cada reacción maestra con sus tres direcciones (LR, RL, BI).
- `rhea2ec.tsv`: correspondencia entre reacciones y números EC.
- `rhea-reactions.txt.gz`: ecuación de cada reacción con sus participantes ChEBI y
  sus números EC, en el formato de texto "KEGG REACTION" que Rhea publica en `txt/`
  (solo el formato: los datos son de Rhea).

Además de descargar, este módulo lee esos archivos para la curaduría de vías.
"""

from __future__ import annotations

import csv
import gzip
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

from metabo.download import Downloader
from metabo.errors import SourceFormatError
from metabo.manifest import DownloadRecord
from metabo.sources.formats import check_header

FUENTE = "rhea"
BASE_URL = "https://ftp.expasy.org/databases/rhea"
RELEASE_URL = f"{BASE_URL}/rhea-release.properties"

# Archivo TSV -> encabezado esperado. Si Rhea cambia las columnas, el extractor se
# detiene en lugar de cargar datos mal interpretados.
TSV_FILES: dict[str, tuple[str, ...]] = {
    "rhea-directions.tsv": ("RHEA_ID_MASTER", "RHEA_ID_LR", "RHEA_ID_RL", "RHEA_ID_BI"),
    "rhea2ec.tsv": ("RHEA_ID", "DIRECTION", "MASTER_ID", "ID"),
}

REACTIONS_FILE = "rhea-reactions.txt.gz"
REACTIONS_URL = f"{BASE_URL}/txt/{REACTIONS_FILE}"

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


def extract(downloader: Downloader, raw_dir: Path) -> tuple[Release, list[DownloadRecord]]:
    """Descarga la versión vigente de Rhea a raw/rhea/<release>/ y devuelve sus registros."""
    release = parse_release(downloader.fetch_text(FUENTE, RELEASE_URL))

    records = [downloader.download(FUENTE, RELEASE_URL, release.numero)]
    for filename, expected in TSV_FILES.items():
        record = downloader.download(FUENTE, f"{BASE_URL}/tsv/{filename}", release.numero)
        check_header(raw_dir / record.archivo, expected)
        records.append(record)
    record = downloader.download(FUENTE, REACTIONS_URL, release.numero)
    check_reactions_file(raw_dir / record.archivo)
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


# ---------------------------------------------------------------------------
# Lectura de los archivos descargados
# ---------------------------------------------------------------------------

_ENTRY = re.compile(r"^RHEA:[0-9]+$")
_CHEBI = re.compile(r"^CHEBI:[0-9]+$")
_COEFFICIENT = re.compile(r"^[0-9]+$")
_EC = re.compile(r"^[1-7]\.[0-9]+\.[0-9]+\.n?[0-9]+$")
# Separadores de la ecuación: "=" (sin dirección, reacción maestra), "=>" y "<=>".
DIRECTIONS = ("=", "=>", "<=>")


@dataclass(frozen=True)
class Participant:
    """Un participante de la ecuación. Los polímeros listan varios ChEBI separados por comas."""

    chebi: tuple[str, ...]
    coeficiente: int


@dataclass(frozen=True)
class Reaction:
    id: str  # CURIE, p. ej. RHEA:16109
    definicion: str
    direccion: str  # uno de DIRECTIONS
    izquierda: tuple[Participant, ...]
    derecha: tuple[Participant, ...]
    ec: tuple[str, ...]  # CURIE, p. ej. EC:2.7.1.11

    @property
    def chebi(self) -> frozenset[str]:
        return frozenset(c for p in self.izquierda + self.derecha for c in p.chebi)


def _parse_side(text: str, entry: str) -> tuple[Participant, ...]:
    participants = []
    for term in text.split(" + "):
        tokens = term.split()
        coefficient = 1
        if len(tokens) == 2 and _COEFFICIENT.match(tokens[0]):
            coefficient = int(tokens[0])
            tokens = tokens[1:]
        ids = tuple(tokens[0].split(",")) if len(tokens) == 1 else ()
        if not ids or not all(_CHEBI.match(i) for i in ids):
            raise SourceFormatError(f"{REACTIONS_FILE}: término no reconocido en {entry}: {term!r}")
        participants.append(Participant(chebi=ids, coeficiente=coefficient))
    return tuple(participants)


def _parse_equation(
    text: str, entry: str
) -> tuple[str, tuple[Participant, ...], tuple[Participant, ...]]:
    for symbol in DIRECTIONS:
        parts = text.split(f" {symbol} ")
        if len(parts) == 2:
            return symbol, _parse_side(parts[0], entry), _parse_side(parts[1], entry)
    raise SourceFormatError(f"{REACTIONS_FILE}: ecuación no reconocida en {entry}: {text!r}")


def _build_reaction(fields: dict[str, list[str]]) -> Reaction:
    entry = " ".join(fields.get("ENTRY", []))
    if not _ENTRY.match(entry):
        raise SourceFormatError(f"{REACTIONS_FILE}: entrada sin ENTRY RHEA válido: {entry!r}")
    for key in ("DEFINITION", "EQUATION"):
        if len(fields.get(key, [])) != 1:
            raise SourceFormatError(f"{REACTIONS_FILE}: {entry} no tiene una línea {key}.")
    direction, left, right = _parse_equation(fields["EQUATION"][0], entry)
    ec = " ".join(fields.get("ENZYME", [])).split()
    if not all(_EC.match(e) for e in ec):
        raise SourceFormatError(f"{REACTIONS_FILE}: número EC no válido en {entry}: {ec}")
    return Reaction(
        id=entry,
        definicion=fields["DEFINITION"][0],
        direccion=direction,
        izquierda=left,
        derecha=right,
        ec=tuple(f"EC:{e}" for e in ec),
    )


def parse_reactions(lines: Iterable[str]) -> Iterator[Reaction]:
    """Lee entradas ENTRY/DEFINITION/EQUATION/ENZYME separadas por '///'.

    Las líneas que empiezan con espacios continúan el campo anterior (ENZYME largos).
    """
    fields: dict[str, list[str]] = {}
    last: str | None = None
    for raw in lines:
        line = raw.rstrip("\r\n")
        if line == "///":
            yield _build_reaction(fields)
            fields, last = {}, None
        elif not line.strip():
            continue
        elif line[0] == " ":
            if last is None:
                raise SourceFormatError(f"{REACTIONS_FILE}: continuación sin campo: {line!r}")
            fields[last][-1] += " " + line.strip()
        else:
            key, _, value = line.partition(" ")
            last = key
            fields.setdefault(key, []).append(value.strip())
    if fields:
        raise SourceFormatError(f"{REACTIONS_FILE}: la última entrada no termina en '///'.")


def read_reactions(path: Path) -> dict[str, Reaction]:
    """Todas las reacciones de rhea-reactions.txt.gz, indexadas por CURIE."""
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return {r.id: r for r in parse_reactions(handle)}


def check_reactions_file(path: Path) -> None:
    """Comprueba que el archivo empiece con una entrada completa en el formato esperado."""
    try:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            head: list[str] = []
            for line in handle:
                head.append(line)
                if line.rstrip("\r\n") == "///":
                    break
    except (OSError, UnicodeDecodeError) as exc:
        raise SourceFormatError(f"No se pudo leer {path.name}: {exc}") from exc
    if not head or not head[0].startswith("ENTRY") or head[-1].rstrip("\r\n") != "///":
        raise SourceFormatError(
            f"{path.name} cambió de formato: se esperaban entradas ENTRY ... /// "
            "(ver txt/README.txt de Rhea) antes de adaptar el extractor."
        )
    list(parse_reactions(head))


def _read_tsv(path: Path) -> Iterator[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def read_masters(path: Path) -> dict[str, str]:
    """rhea-directions.tsv: cada ID (maestro, LR, RL o BI) -> su reacción maestra (CURIE)."""
    masters: dict[str, str] = {}
    for row in _read_tsv(path):
        master = f"RHEA:{row['RHEA_ID_MASTER']}"
        for column in TSV_FILES["rhea-directions.tsv"]:
            masters[f"RHEA:{row[column]}"] = master
    return masters


def read_rhea2ec(path: Path) -> dict[str, frozenset[str]]:
    """rhea2ec.tsv: reacción maestra (CURIE) -> números EC (CURIE)."""
    links: dict[str, set[str]] = {}
    for row in _read_tsv(path):
        links.setdefault(f"RHEA:{row['MASTER_ID']}", set()).add(f"EC:{row['ID']}")
    return {k: frozenset(v) for k, v in links.items()}


def read_directions(path: Path) -> dict[str, tuple[str, str, str]]:
    """rhea-directions.tsv: reacción maestra (CURIE) -> (LR, RL, BI) en CURIE."""
    return {
        f"RHEA:{row['RHEA_ID_MASTER']}": (
            f"RHEA:{row['RHEA_ID_LR']}",
            f"RHEA:{row['RHEA_ID_RL']}",
            f"RHEA:{row['RHEA_ID_BI']}",
        )
        for row in _read_tsv(path)
    }

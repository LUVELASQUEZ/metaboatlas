"""Extractor de NCBI Taxonomy (sección 3 de docs/MANUAL.md): linaje y rangos.

Descarga del FTP oficial (`pub/taxonomy/new_taxdump/`):

- `new_taxdump.tar.gz.md5`: suma MD5 publicada del archivo.
- `new_taxdump.tar.gz`: volcado completo de la taxonomía (formato en
  `taxdump_readme.txt`). Se usan `taxidlineage.dmp`, `names.dmp`, `nodes.dmp`,
  `merged.dmp` y `delnodes.dmp`.

NCBI regenera el volcado a diario y no le pone número de versión. La versión es la
fecha (AAAA-MM-DD, UTC) de la cabecera Last-Modified del archivo MD5, que se publica
junto con el volcado. Si NCBI publica otro volcado durante la descarga, la suma MD5
no coincide y la extracción se detiene.
"""

from __future__ import annotations

import hashlib
import re
import tarfile
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import IO

import httpx

from metabo.download import Downloader
from metabo.errors import ConfigError, SourceFormatError
from metabo.manifest import DownloadRecord

FUENTE = "ncbi_taxonomy"
BASE_URL = "https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/new_taxdump"
ARCHIVE = "new_taxdump.tar.gz"
ARCHIVE_URL = f"{BASE_URL}/{ARCHIVE}"
MD5_URL = f"{ARCHIVE_URL}.md5"

# Archivos del volcado que usa el pipeline.
MEMBERS = ("delnodes.dmp", "merged.dmp", "names.dmp", "nodes.dmp", "taxidlineage.dmp")

_MD5_LINE = re.compile(rf"^([0-9a-f]{{32}})\s+{re.escape(ARCHIVE)}\s*$")

# Nombre científico del nodo de rango "domain" -> valor de `dominio` en el esquema.
DOMINIOS = {"Bacteria": "bacteria", "Archaea": "arquea", "Eukaryota": "eucariota"}


def version_of(headers: httpx.Headers, url: str) -> str:
    """Fecha (AAAA-MM-DD, UTC) de la cabecera Last-Modified."""
    value = headers.get("Last-Modified")
    if not value:
        raise SourceFormatError(
            f"La respuesta de {url} no trae la cabecera Last-Modified; sin ella no se "
            "puede fechar el volcado."
        )
    try:
        return parsedate_to_datetime(value).date().isoformat()
    except (TypeError, ValueError) as exc:
        raise SourceFormatError(f"Last-Modified de {url} no es una fecha: {value!r}") from exc


def parse_md5(text: str) -> str:
    """Suma MD5 de `new_taxdump.tar.gz.md5` ("<md5>  new_taxdump.tar.gz")."""
    match = _MD5_LINE.match(text.strip())
    if not match:
        raise SourceFormatError(
            f"{ARCHIVE}.md5 cambió de formato: se esperaba '<md5>  {ARCHIVE}' y se "
            f"encontró {text.strip()[:80]!r}."
        )
    return match.group(1)


def md5_of(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_archive(path: Path) -> None:
    """Comprueba que el volcado tenga los archivos que usa el pipeline."""
    try:
        with tarfile.open(path, "r:gz") as tar:
            names = set(tar.getnames())
    except (OSError, tarfile.TarError) as exc:
        raise SourceFormatError(f"No se pudo leer {path.name}: {exc}") from exc
    missing = [m for m in MEMBERS if m not in names]
    if missing:
        raise SourceFormatError(
            f"{path.name} cambió de contenido: no tiene {', '.join(missing)}. Revisa "
            "taxdump_readme.txt antes de adaptar el extractor."
        )


def extract(downloader: Downloader, raw_dir: Path) -> tuple[str, list[DownloadRecord]]:
    """Descarga el volcado vigente a raw/ncbi_taxonomy/<AAAA-MM-DD>/ y verifica su MD5."""
    text, headers = downloader.fetch_text_with_headers(FUENTE, MD5_URL)
    version = version_of(headers, MD5_URL)
    expected = parse_md5(text)

    md5_record = downloader.download(FUENTE, MD5_URL, version)
    archive_record = downloader.download(FUENTE, ARCHIVE_URL, version)
    published = parse_md5((raw_dir / md5_record.archivo).read_text(encoding="utf-8"))
    actual = md5_of(raw_dir / archive_record.archivo)
    if published != expected or actual != expected:
        raise SourceFormatError(
            f"La suma MD5 de {ARCHIVE} ({actual}) no coincide con la publicada "
            f"({published}). NCBI pudo publicar un volcado nuevo durante la descarga; "
            "vuelve a ejecutar la extracción."
        )
    check_archive(raw_dir / archive_record.archivo)
    return version, [md5_record, archive_record]


# ---------------------------------------------------------------------------
# Lectura del volcado
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TaxonNode:
    taxon: str  # CURIE, p. ej. taxon:562
    nombre: str
    rango: str


@dataclass(frozen=True)
class TaxonRecord:
    taxon: str
    nombre_cientifico: str
    rango: str
    linaje: tuple[TaxonNode, ...]  # desde el nodo más lejano hasta el padre inmediato
    dominio: str | None  # bacteria, arquea, eucariota; None si el linaje no tiene dominio


def _rows(handle: IO[bytes]) -> Iterator[list[str]]:
    """Filas de un .dmp: campos separados por "\\t|\\t" y línea terminada en "\\t|"."""
    for line in handle:
        yield line.decode("utf-8").rstrip("\n").removesuffix("\t|").split("\t|\t")


def _members(path: Path, wanted: Iterable[str]) -> Iterator[tuple[str, IO[bytes]]]:
    """Recorre el volcado una sola vez y entrega los archivos pedidos, en su orden."""
    wanted = set(wanted)
    with tarfile.open(path, "r:gz") as tar:
        for member in tar:
            if member.name in wanted:
                handle = tar.extractfile(member)
                if handle is None:
                    raise SourceFormatError(f"{member.name} no es un archivo en {path.name}.")
                yield member.name, handle


def _number(curie: str) -> str:
    if not re.fullmatch(r"taxon:[1-9][0-9]*", curie):
        raise ConfigError(f"{curie!r} no es un taxón en formato CURIE (taxon:<número>).")
    return curie.split(":", 1)[1]


def read_taxa(path: Path, taxa: Iterable[str]) -> dict[str, TaxonRecord]:
    """Nombre, rango, linaje y dominio de cada taxón pedido (CURIE).

    Lanza ConfigError si un taxón no existe, se eliminó o se fusionó con otro: hay que
    corregir organismos.yaml, no adivinar el reemplazo.
    """
    requested = {_number(t) for t in taxa}

    # 1.ª pasada: taxidlineage.dmp está al final del volcado.
    lineages: dict[str, list[str]] = {}
    for _, handle in _members(path, ["taxidlineage.dmp"]):
        for row in _rows(handle):
            if row[0] in requested:
                lineages[row[0]] = row[1].split()

    # 2.ª pasada: fusionados, eliminados, nombres científicos y rangos.
    needed = requested | {t for lineage in lineages.values() for t in lineage}
    merged: dict[str, str] = {}
    deleted: set[str] = set()
    names: dict[str, str] = {}
    ranks: dict[str, str] = {}
    for name, handle in _members(path, ["merged.dmp", "delnodes.dmp", "names.dmp", "nodes.dmp"]):
        for row in _rows(handle):
            if name == "merged.dmp" and row[0] in requested:
                merged[row[0]] = row[1]
            elif name == "delnodes.dmp" and row[0] in requested:
                deleted.add(row[0])
            elif name == "names.dmp" and row[0] in needed and row[3] == "scientific name":
                names[row[0]] = row[1]
            elif name == "nodes.dmp" and row[0] in needed:
                ranks[row[0]] = row[2]

    errors = []
    for number in sorted(requested, key=int):
        if number in merged:
            errors.append(f"taxon:{number} se fusionó con taxon:{merged[number]}")
        elif number in deleted:
            errors.append(f"taxon:{number} se eliminó")
        elif number not in lineages or number not in names or number not in ranks:
            errors.append(f"taxon:{number} no existe")
    if errors:
        raise ConfigError(
            f"Taxones de organismos.yaml que no sirven según {path.name}: "
            + "; ".join(errors)
            + ". Corrige organismos.yaml."
        )

    missing = sorted((needed - names.keys()) | (needed - ranks.keys()), key=int)
    if missing:
        raise SourceFormatError(
            f"{path.name} es incoherente: el linaje cita nodos sin nombre o sin rango "
            f"({', '.join(missing[:5])})."
        )

    records = {}
    for number in requested:
        lineage = tuple(TaxonNode(f"taxon:{t}", names[t], ranks[t]) for t in lineages[number])
        domains = [n.nombre for n in lineage if n.rango == "domain"]
        unknown = [d for d in domains if d not in DOMINIOS]
        if unknown:
            raise SourceFormatError(
                f"taxon:{number} tiene un dominio desconocido en {path.name}: {unknown}."
            )
        records[f"taxon:{number}"] = TaxonRecord(
            taxon=f"taxon:{number}",
            nombre_cientifico=names[number],
            rango=ranks[number],
            linaje=lineage,
            dominio=DOMINIOS[domains[0]] if domains else None,
        )
    return records

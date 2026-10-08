"""Extractor de Europe PMC (sección 3 de docs/MANUAL.md): datos de cita de artículos.

Consulta la API REST oficial (`www.ebi.ac.uk/europepmc/webservices/rest/search`) por
los PMID de curation/referencias.yaml y guarda cada respuesta JSON tal cual en
raw/europe_pmc/<AAAA-MM-DD>/. Usa `resultType=lite`, que no trae resúmenes: por
decisión del 2026-10-08 solo se toman datos de cita (título, autores, revista, año,
DOI, PMCID), nunca resúmenes ni texto de los artículos, que tienen copyright de cada
editorial (https://europepmc.org/Copyright).

Europe PMC no publica versiones de sus datos: la versión es la fecha de la consulta.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlencode

from metabo.download import Downloader
from metabo.errors import SourceFormatError
from metabo.manifest import DownloadRecord

FUENTE = "europe_pmc"
ENDPOINT = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
LOTE = 50
_PMID = re.compile(r"^[1-9][0-9]{0,8}$")


@dataclass(frozen=True)
class Article:
    """Datos de cita de un artículo, tal como los da Europe PMC."""

    pmid: str
    titulo: str
    autores: str
    revista: str
    anio: int
    volumen: str | None
    numero: str | None
    paginas: str | None
    doi: str | None
    pmcid: str | None
    acceso_abierto: bool


def query(pmids: Iterable[str]) -> str:
    ids = []
    for pmid in pmids:
        if not _PMID.match(pmid):
            raise ValueError(f"{pmid!r} no es un PMID.")
        ids.append(f"EXT_ID:{pmid}")
    return f"({' OR '.join(ids)}) AND SRC:MED"


def query_url(pmids: Iterable[str]) -> str:
    params = {"query": query(pmids), "format": "json", "resultType": "lite", "pageSize": 100}
    return f"{ENDPOINT}?{urlencode(params)}"


def batches(pmids: Iterable[str]) -> list[tuple[str, list[str]]]:
    """Lotes ordenados de PMID y el nombre de archivo de cada uno (referencias-001.json)."""
    ordered = sorted(set(pmids), key=int)
    return [
        (f"referencias-{n:03d}.json", ordered[start : start + LOTE])
        for n, start in enumerate(range(0, len(ordered), LOTE), start=1)
    ]


def check_response(text: str, archivo: str, expected: Iterable[str] = ()) -> list[dict]:
    """Resultados de una respuesta; exige que estén todos los PMID pedidos."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SourceFormatError(f"{archivo} no es JSON: {exc}") from exc
    results = data.get("resultList", {}).get("result") if isinstance(data, dict) else None
    if not isinstance(results, list):
        raise SourceFormatError(f"{archivo} no tiene resultList.result.")
    for row in results:
        if not isinstance(row, dict) or not {"pmid", "title", "pubYear"} <= set(row):
            raise SourceFormatError(f"{archivo}: un resultado no tiene pmid, title y pubYear.")
        if "abstractText" in row:
            raise SourceFormatError(f"{archivo} trae resúmenes: solo se usan datos de cita.")
    missing = set(expected) - {row["pmid"] for row in results}
    if missing:
        raise SourceFormatError(
            f"Europe PMC no tiene los PMID {', '.join(sorted(missing, key=int))}: "
            "revisa curation/referencias.yaml (nunca se inventan identificadores)."
        )
    return results


def extract(
    downloader: Downloader, raw_dir: Path, pmids: Iterable[str], today: date | None = None
) -> tuple[str, list[DownloadRecord]]:
    """Consulta los datos de cita de `pmids` y los guarda en raw/europe_pmc/<fecha>/."""
    today = today or date.today()
    version = today.isoformat()
    records = []
    for archivo, lote in batches(pmids):
        record = downloader.download(
            FUENTE, query_url(lote), version, filename=archivo, today=today
        )
        check_response((raw_dir / record.archivo).read_text(encoding="utf-8"), archivo, lote)
        records.append(record)
    if not records:
        raise SourceFormatError("curation/referencias.yaml no tiene ningún PMID que consultar.")
    return version, records


def _text(value: object) -> str | None:
    """Texto sin etiquetas HTML (Europe PMC marca así las cursivas: <i>E. coli</i>)."""
    text = re.sub(r"<[^>]+>", "", str(value)).strip() if value is not None else ""
    return text or None


def read_articles(paths: Iterable[Path]) -> dict[str, Article]:
    """PMID -> datos de cita de los archivos descargados."""
    articles = {}
    for path in paths:
        for row in check_response(path.read_text(encoding="utf-8"), path.name):
            pmid = row["pmid"]
            articles[pmid] = Article(
                pmid=pmid,
                titulo=_text(row["title"]) or "",
                autores=_text(row.get("authorString")) or "",
                revista=_text(row.get("journalTitle")) or "",
                anio=int(row["pubYear"]),
                volumen=_text(row.get("journalVolume")),
                numero=_text(row.get("issue")),
                paginas=_text(row.get("pageInfo")),
                doi=_text(row.get("doi")),
                pmcid=_text(row.get("pmcid")),
                acceso_abierto=row.get("isOpenAccess") == "Y",
            )
    return articles

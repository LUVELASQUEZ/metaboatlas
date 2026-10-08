"""Extractor de Wikidata (sección 3 de docs/MANUAL.md): nombres en español.

Consulta el servicio SPARQL oficial (WDQS) por los compuestos (propiedad P683, ID de
ChEBI) y las enzimas (P591, número EC) que usa el paquete, y guarda cada respuesta
JSON tal cual en raw/wikidata/<AAAA-MM-DD>/. Los datos estructurados de Wikidata son
CC0 (https://www.wikidata.org/wiki/Wikidata:Licensing).

Sigue las reglas de acceso de Wikidata:Data_access: User-Agent con contacto (lo pone
el Downloader), gzip, una consulta a la vez y lotes de a lo sumo `LOTE` IDs.

Wikidata no tiene versiones: la versión es la fecha de la consulta.

Un nombre solo se usa si el ID tiene exactamente una etiqueta en español distinta.
Si un número EC o un ChEBI aparece en varios elementos con etiquetas diferentes
(por ejemplo, EC 2.7.1.1 está en "hexocinasa" y en "glucocinasa"), es ambiguo y no
se usa: el nombre queda para la curaduría manual (curation/nombres_es.yaml).
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlencode

from metabo.download import Downloader
from metabo.errors import SourceFormatError
from metabo.manifest import DownloadRecord

FUENTE = "wikidata"
ENDPOINT = "https://query.wikidata.org/sparql"
LOTE = 200

# Tipo -> (prefijo CURIE, propiedad de Wikidata cuyo valor es el ID sin prefijo).
TIPOS: dict[str, tuple[str, str]] = {
    "compuestos": ("CHEBI", "P683"),
    "enzimas": ("EC", "P591"),
}

_QUERY = """SELECT ?id ?item ?es WHERE {{
  VALUES ?id {{ {values} }}
  ?item wdt:{prop} ?id .
  OPTIONAL {{ ?item rdfs:label ?es . FILTER(LANG(?es) = "es") }}
}}"""


@dataclass(frozen=True)
class Label:
    """Nombre en español de un ID y el elemento de Wikidata del que sale."""

    qid: str
    es: str


def query(tipo: str, ids: Iterable[str]) -> str:
    """Consulta SPARQL para un lote de CURIEs de un tipo (compuestos o enzimas)."""
    prefix, prop = TIPOS[tipo]
    natives = []
    for curie in ids:
        head, _, native = curie.partition(":")
        if head != prefix or not native or '"' in native or "\\" in native:
            raise ValueError(f"{curie} no es un ID {prefix} válido para consultar Wikidata.")
        natives.append(native)
    values = " ".join(json.dumps(n) for n in natives)
    return _QUERY.format(values=values, prop=prop)


def query_url(tipo: str, ids: Iterable[str]) -> str:
    return f"{ENDPOINT}?{urlencode({'query': query(tipo, ids), 'format': 'json'})}"


def file_names(tipo: str, ids: Iterable[str]) -> list[tuple[str, list[str]]]:
    """Lotes ordenados de IDs y el nombre de archivo de cada uno (compuestos-001.json)."""
    ordered = sorted(set(ids))
    return [
        (f"{tipo}-{n:03d}.json", ordered[start : start + LOTE])
        for n, start in enumerate(range(0, len(ordered), LOTE), start=1)
    ]


def check_response(text: str, archivo: str) -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SourceFormatError(f"{archivo} no es JSON: {exc}") from exc
    if not isinstance(data, dict) or set(data.get("head", {}).get("vars", [])) != {
        "id",
        "item",
        "es",
    }:
        raise SourceFormatError(
            f"{archivo} no tiene el formato SPARQL JSON esperado (head.vars = id, item, es)."
        )
    if not isinstance(data.get("results", {}).get("bindings"), list):
        raise SourceFormatError(f"{archivo} no tiene results.bindings.")
    return data


def extract(
    downloader: Downloader,
    raw_dir: Path,
    compuestos: Iterable[str],
    enzimas: Iterable[str],
    today: date | None = None,
) -> tuple[str, list[DownloadRecord]]:
    """Consulta los nombres de `compuestos` (CHEBI:…) y `enzimas` (EC:…) y los guarda."""
    today = today or date.today()
    version = today.isoformat()
    records = []
    for tipo, ids in (("compuestos", compuestos), ("enzimas", enzimas)):
        for archivo, lote in file_names(tipo, ids):
            record = downloader.download(
                FUENTE, query_url(tipo, lote), version, filename=archivo, today=today
            )
            check_response((raw_dir / record.archivo).read_text(encoding="utf-8"), archivo)
            records.append(record)
    if not records:
        raise SourceFormatError("No hay compuestos ni enzimas que consultar en Wikidata.")
    return version, records


def read_labels(paths: Iterable[Path], tipo: str) -> dict[str, Label]:
    """CURIE -> nombre en español, solo si el ID tiene una única etiqueta en español."""
    prefix, _ = TIPOS[tipo]
    found: dict[str, dict[str, set[str]]] = {}
    for path in paths:
        data = check_response(path.read_text(encoding="utf-8"), path.name)
        for row in data["results"]["bindings"]:
            curie = f"{prefix}:{row['id']['value']}"
            labels = found.setdefault(curie, {})
            qid = row["item"]["value"].rsplit("/", 1)[-1]
            if "es" in row:
                labels.setdefault(row["es"]["value"].strip(), set()).add(qid)
    result = {}
    for curie, labels in found.items():
        if len(labels) == 1:
            ((es, qids),) = labels.items()
            result[curie] = Label(qid=min(qids, key=lambda q: int(q.lstrip("Q"))), es=es)
    return result

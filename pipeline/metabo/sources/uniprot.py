"""Extractor de UniProtKB (sección 3 de docs/MANUAL.md): enzimas por organismo.

Para cada organismo de `pipeline/organismos.yaml` descarga, de la API REST oficial:

- `<UP>.json`: la ficha de su proteoma de referencia (`rest.uniprot.org/proteomes/<UP>`),
  con el taxón con que UniProt lo registra y su número de proteínas.
- `<UP>.tsv.gz`: todas sus proteínas, revisadas (Swiss-Prot) y no revisadas (TrEMBL),
  con los campos de `FIELDS` (`rest.uniprot.org/uniprotkb/stream`, consulta
  `proteome:<UP>`). Las no revisadas hacen falta para la evidencia media de la
  sección 5 del manual.

Las proteínas se piden siempre por proteoma, no por taxón (ver organismos.yaml).
La versión es el release de UniProt que la API declara en la cabecera
`X-UniProt-Release` (por ejemplo 2026_03); cada respuesta debe traer el mismo, o la
extracción se detiene.
"""

from __future__ import annotations

import gzip
import json
from collections.abc import Sequence
from pathlib import Path
from urllib.parse import urlencode

import httpx

from metabo.download import Downloader
from metabo.errors import ConfigError, SourceFormatError
from metabo.manifest import DownloadRecord
from metabo.organisms import Organism, load_organisms
from metabo.sources.formats import check_header

FUENTE = "uniprot"
BASE_URL = "https://rest.uniprot.org"
RELEASE_HEADER = "X-UniProt-Release"
REFERENCE_PROTEOME = "Reference proteome"

# Campo de la API -> encabezado de su columna en el TSV (comprobados contra
# rest.uniprot.org/configure/uniprotkb/result-fields y una descarga del release 2026_03).
FIELDS: dict[str, str] = {
    "accession": "Entry",
    "protein_name": "Protein names",
    "gene_names": "Gene Names",
    "organism_id": "Organism (ID)",
    "ec": "EC number",
    "rhea": "Rhea ID",
    "cc_catalytic_activity": "Catalytic activity",
    "cc_cofactor": "Cofactor",
    "cc_pathway": "Pathway",
    "go_p": "Gene Ontology (biological process)",
    "reviewed": "Reviewed",
    "annotation_score": "Annotation",
    "xref_kegg": "KEGG",
    "xref_reactome": "Reactome",
    "xref_pdb": "PDB",
    "xref_alphafolddb": "AlphaFoldDB",
}


def proteome_url(proteome: str) -> str:
    return f"{BASE_URL}/proteomes/{proteome}?format=json"


def proteins_url(proteome: str) -> str:
    query = {
        "query": f"proteome:{proteome}",
        "fields": ",".join(FIELDS),
        "format": "tsv",
        "compressed": "true",
    }
    return f"{BASE_URL}/uniprotkb/stream?{urlencode(query)}"


def release_of(headers: httpx.Headers, url: str) -> str:
    release = headers.get(RELEASE_HEADER, "").strip()
    if not release:
        raise SourceFormatError(
            f"La respuesta de {url} no trae la cabecera {RELEASE_HEADER}; sin ella no se "
            "puede registrar la versión de UniProt."
        )
    return release


def _same_release(version: str, url: str):
    def check(headers: httpx.Headers) -> None:
        found = release_of(headers, url)
        # Si UniProt publicó un release durante la extracción, las versiones no coinciden.
        if found != version:
            raise SourceFormatError(
                f"{url} respondió con el release {found}, pero se esperaba {version}; "
                "vuelve a ejecutar la extracción."
            )

    return check


def check_proteome(path: Path, proteome: str) -> int:
    """Comprueba la ficha del proteoma y devuelve su número de proteínas."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceFormatError(f"No se pudo leer {path.name}: {exc}") from exc
    if not isinstance(data, dict) or data.get("id") != proteome:
        raise SourceFormatError(f"{path.name} no es la ficha del proteoma {proteome}.")
    if data.get("proteomeType") != REFERENCE_PROTEOME:
        raise SourceFormatError(
            f"{proteome} ya no es un proteoma de referencia en UniProt "
            f"(proteomeType: {data.get('proteomeType')!r}). Revisa organismos.yaml."
        )
    count = data.get("proteinCount")
    if not isinstance(count, int) or count < 0:
        raise SourceFormatError(f"{path.name} no declara un proteinCount válido: {count!r}")
    return count


def count_rows(path: Path) -> int:
    """Filas de datos (sin el encabezado) de un TSV comprimido."""
    try:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            return sum(1 for line in handle if line.strip()) - 1
    except (OSError, UnicodeDecodeError) as exc:
        raise SourceFormatError(f"No se pudo leer {path.name}: {exc}") from exc


def extract(
    downloader: Downloader,
    raw_dir: Path,
    organisms: Sequence[Organism] | None = None,
) -> tuple[str, list[DownloadRecord]]:
    """Descarga los proteomas de la lista de organismos a raw/uniprot/<release>/."""
    organisms = list(load_organisms() if organisms is None else organisms)
    missing = [o.id for o in organisms if o.proteoma_referencia is None]
    if missing:
        raise ConfigError(
            "Estos organismos no tienen proteoma_referencia en organismos.yaml y no se "
            f"pueden descargar de UniProt: {', '.join(missing)}."
        )
    proteomes = [o.proteoma_referencia for o in organisms if o.proteoma_referencia]

    first = proteome_url(proteomes[0])
    _, headers = downloader.fetch_text_with_headers(FUENTE, first, max_bytes=1 << 22)
    version = release_of(headers, first)

    records = []
    for proteome in proteomes:
        url = proteome_url(proteome)
        record = downloader.download(
            FUENTE, url, version, f"{proteome}.json", check_headers=_same_release(version, url)
        )
        expected = check_proteome(raw_dir / record.archivo, proteome)
        records.append(record)

        url = proteins_url(proteome)
        record = downloader.download(
            FUENTE, url, version, f"{proteome}.tsv.gz", check_headers=_same_release(version, url)
        )
        path = raw_dir / record.archivo
        check_header(path, tuple(FIELDS.values()))
        # El stream de UniProt puede cortarse sin error; el número de filas lo delata.
        rows = count_rows(path)
        if rows != expected:
            raise SourceFormatError(
                f"{path.name} tiene {rows} proteínas, pero el proteoma {proteome} declara "
                f"{expected}. La descarga pudo quedar incompleta; vuelve a ejecutarla."
            )
        records.append(record)
    return version, records

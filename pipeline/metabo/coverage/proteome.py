"""Lectura de los proteomas de UniProt descargados en raw/ para el cálculo de cobertura.

Cada proteoma es `raw/uniprot/<release>/<UP>.tsv.gz` (extractor de UniProt). Se usan
cuatro columnas: `Entry`, `Reviewed`, `EC number` (separados por "; ") y `Rhea ID`
(separados por espacios). Formato comprobado con el release 2026_03.
"""

from __future__ import annotations

import csv
import gzip
from collections.abc import Iterator
from pathlib import Path

from metabo.coverage.algorithm import Protein
from metabo.errors import SourceFormatError

COLUMNS = ("Entry", "Reviewed", "EC number", "Rhea ID")
REVIEWED = {"reviewed": True, "unreviewed": False}


def _split(value: str, sep: str | None) -> list[str]:
    return [v.strip() for v in value.split(sep) if v.strip()]


def read_proteins(path: Path) -> Iterator[Protein]:
    """Proteínas de un TSV de UniProt, con accesiones, EC y Rhea en formato CURIE."""
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        missing = [c for c in COLUMNS if c not in (reader.fieldnames or ())]
        if missing:
            raise SourceFormatError(f"{path.name} no tiene las columnas {', '.join(missing)}.")
        for line, row in enumerate(reader, start=2):
            reviewed = REVIEWED.get(row["Reviewed"])
            if reviewed is None:
                raise SourceFormatError(
                    f"{path.name}, línea {line}: valor inesperado en Reviewed: {row['Reviewed']!r}."
                )
            rhea = _split(row["Rhea ID"], None)
            bad = [r for r in rhea if not r.startswith("RHEA:")]
            if bad:
                raise SourceFormatError(
                    f"{path.name}, línea {line}: IDs Rhea sin prefijo RHEA: {bad}."
                )
            yield Protein(
                accession=f"UNIPROT:{row['Entry']}",
                revisada=reviewed,
                rhea=frozenset(rhea),
                ec=frozenset(f"EC:{ec}" for ec in _split(row["EC number"], ";")),
            )

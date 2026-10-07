"""Cobertura de cada vía curada en cada organismo, a partir de raw/ (etapa "calcular").

Produce un documento por vía y organismo que cumple schema/cobertura.schema.json y se
escribe en `data/<version_datos>/cobertura/<slug>/<taxon>.json` (sección 6 del manual).
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from metabo import schemas
from metabo.config import CoverageThresholds
from metabo.coverage.algorithm import ProteomeIndex, Step, Thresholds, pathway_coverage
from metabo.coverage.proteome import read_proteins
from metabo.errors import ConfigError
from metabo.manifest import Manifest
from metabo.organisms import Organism
from metabo.sources import rhea


@dataclass(frozen=True)
class CoverageInputs:
    """Datos descargados que necesita el cálculo: versiones, Rhea maestro y proteomas."""

    versiones: dict[str, str]
    maestras: dict[str, str]
    proteomas: dict[str, Path]

    @classmethod
    def from_raw(cls, raw_dir: Path, organisms: Iterable[Organism]) -> CoverageInputs:
        manifest_path = raw_dir / "manifest.json"
        if not manifest_path.is_file():
            raise ConfigError(
                f"No existe {manifest_path}: descarga primero rhea y uniprot "
                "con `uv run metabo extraer <fuente>`."
            )
        manifest = Manifest.read(manifest_path)
        organisms = list(organisms)
        without = [o.id for o in organisms if o.proteoma_referencia is None]
        if without:
            raise ConfigError(
                f"Sin proteoma de referencia en organismos.yaml: {', '.join(without)}."
            )
        proteome_files = [f"{o.proteoma_referencia}.tsv.gz" for o in organisms]
        rhea_version, rhea_files = manifest.latest("rhea", ("rhea-directions.tsv",))
        uniprot_version, uniprot_files = manifest.latest("uniprot", proteome_files)
        return cls(
            versiones={"uniprot": uniprot_version, "rhea": rhea_version},
            maestras=rhea.read_masters(raw_dir / rhea_files["rhea-directions.tsv"]),
            proteomas={
                o.id: raw_dir / uniprot_files[name]
                for o, name in zip(organisms, proteome_files, strict=True)
            },
        )


def thresholds(config: CoverageThresholds) -> Thresholds:
    return Thresholds(config.completa, config.casi_completa, config.parcial)


def coverage_document(
    via: Mapping[str, Any],
    taxon: str,
    index: ProteomeIndex,
    umbrales: Thresholds,
    versiones: Mapping[str, str],
    calculado: date,
) -> dict[str, Any]:
    """Documento de cobertura de una vía en un organismo, validado contra el esquema."""
    steps = [Step.from_curation(p) for p in via["pasos"]]
    result = pathway_coverage(steps, index, umbrales)
    document = {
        "via": via["id"],
        "taxon": taxon,
        "cobertura": result.cobertura,
        "clase": result.clase,
        "pasos": {sid: r.as_json() for sid, r in result.pasos.items()},
        "modo": "precalculado",
        "calculado": calculado.isoformat(),
        "fuentes": dict(versiones),
    }
    schemas.validate("cobertura", document, label=f"cobertura de {via['id']} en {taxon}")
    return document


def compute_all(
    vias: Sequence[Mapping[str, Any]],
    organisms: Sequence[Organism],
    inputs: CoverageInputs,
    umbrales: Thresholds,
    calculado: date,
) -> list[dict[str, Any]]:
    """Cobertura de cada vía en cada organismo. Cada proteoma se lee una sola vez."""
    documents = []
    for organism in organisms:
        proteins = read_proteins(inputs.proteomas[organism.id])
        index = ProteomeIndex(proteins, inputs.maestras)
        for via in vias:
            documents.append(
                coverage_document(via, organism.id, index, umbrales, inputs.versiones, calculado)
            )
    return documents


def output_path(out_dir: Path, document: Mapping[str, Any]) -> Path:
    slug = document["via"].split(":", 1)[1]
    taxon = document["taxon"].split(":", 1)[1]
    return out_dir / "cobertura" / slug / f"{taxon}.json"


def write_documents(documents: Iterable[Mapping[str, Any]], out_dir: Path) -> list[Path]:
    paths = []
    for document in documents:
        path = output_path(out_dir, document)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", "utf-8")
        paths.append(path)
    return paths

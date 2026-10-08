"""Referencias bibliográficas del paquete: curation/referencias.yaml + Europe PMC.

La curaduría dice qué PMID se cita y qué afirmación respalda; Europe PMC aporta sus
datos de cita (sin resúmenes ni texto, por decisión del 2026-10-08).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from metabo.errors import ConfigError
from metabo.sources import europe_pmc


class CitedReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    pmid: str = Field(pattern=r"^[1-9][0-9]*$")
    respalda: str = Field(min_length=1)
    verificado: str

    @field_validator("verificado")
    @classmethod
    def _known(cls, value: str) -> str:
        if value not in ("resumen", "texto completo"):
            raise ValueError("debe ser 'resumen' o 'texto completo'")
        return value


def load_curation(path: Path) -> list[CitedReference]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    try:
        references = [CitedReference.model_validate(r) for r in data.get("referencias") or []]
    except ValueError as exc:
        raise ConfigError(f"{path.name} no es válido: {exc}") from exc
    repeated = {r.pmid for r in references if [x.pmid for x in references].count(r.pmid) > 1}
    if repeated:
        raise ConfigError(f"{path.name}: PMID repetidos {', '.join(sorted(repeated))}.")
    return references


@dataclass(frozen=True)
class Provenance:
    version: str
    fecha_descarga: str


def document(
    reference: CitedReference, article: europe_pmc.Article, provenance: Provenance
) -> dict[str, Any]:
    return {
        "id": f"PMID:{article.pmid}",
        "titulo": article.titulo,
        "autores": article.autores,
        "revista": article.revista,
        "anio": article.anio,
        "volumen": article.volumen,
        "numero": article.numero,
        "paginas": article.paginas,
        "doi": article.doi,
        "pmcid": article.pmcid,
        "acceso_abierto": article.acceso_abierto,
        "respalda": " ".join(reference.respalda.split()),
        "verificado": reference.verificado,
        "xrefs": [{"fuente": europe_pmc.FUENTE, "tipo": "articulo", "id": article.pmid}],
        "procedencia": [
            {
                "fuente": europe_pmc.FUENTE,
                "id": article.pmid,
                "version": provenance.version,
                "fecha_descarga": provenance.fecha_descarga,
            }
        ],
    }

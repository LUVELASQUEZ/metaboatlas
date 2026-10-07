"""Lista curada de organismos (pipeline/organismos.yaml).

El código no asume un número fijo de organismos.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from metabo.errors import ConfigError
from metabo.paths import PIPELINE_DIR
from metabo.yamlio import load_yaml

DEFAULT_ORGANISMS_PATH = PIPELINE_DIR / "organismos.yaml"


class Organism(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^taxon:[1-9][0-9]*$")
    nombre: str = Field(min_length=1)
    intereses: list[Literal["modelo", "clinico", "industrial"]] = Field(min_length=1)
    proteoma_referencia: str | None = Field(default=None, pattern=r"^UP[0-9]{9}$")
    nombre_ncbi: str | None = Field(default=None, min_length=1)

    @property
    def taxon_id(self) -> str:
        """ID numérico de NCBI Taxonomy, sin prefijo (por ejemplo 511145)."""
        return self.id.split(":", 1)[1]


class OrganismList(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    organismos: list[Organism] = Field(min_length=1)

    @field_validator("organismos")
    @classmethod
    def _unique_ids(cls, value: list[Organism]) -> list[Organism]:
        seen: set[str] = set()
        for organism in value:
            if organism.id in seen:
                raise ValueError(f"El organismo {organism.id} está repetido.")
            seen.add(organism.id)
        return value


def load_organisms(path: Path = DEFAULT_ORGANISMS_PATH) -> list[Organism]:
    try:
        return list(OrganismList.model_validate(load_yaml(path)).organismos)
    except ValidationError as exc:
        raise ConfigError(f"{path} no es válido:\n{exc}") from exc

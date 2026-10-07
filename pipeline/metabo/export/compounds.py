"""Clase y papel de cada compuesto según curation/compuestos.yaml y la ontología de ChEBI."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from metabo.errors import ConfigError
from metabo.sources.chebi import ancestors
from metabo.yamlio import load_yaml

Clase = Literal["carbohidrato", "lipido", "aminoacido", "nucleotido", "cofactor", "ion_gas", "otro"]
_CHEBI = r"^CHEBI:[1-9][0-9]*$"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Node(_Strict):
    id: str = Field(pattern=_CHEBI)
    nombre: str = Field(min_length=1)


class ClassRule(_Strict):
    clase: Literal["carbohidrato", "lipido", "aminoacido", "nucleotido", "ion_gas"]
    ancestros: list[Node] = Field(min_length=1)


class CompoundCuration(_Strict):
    clases: list[ClassRule] = Field(min_length=1)
    cofactores: list[Node]

    @property
    def nodes(self) -> list[Node]:
        return [n for rule in self.clases for n in rule.ancestros] + list(self.cofactores)


def load_curation(path: Path) -> CompoundCuration:
    try:
        return CompoundCuration.model_validate(load_yaml(path))
    except ValidationError as exc:
        raise ConfigError(f"{path} no es válido:\n{exc}") from exc


def check_names(curation: CompoundCuration, names: Mapping[str, str]) -> list[str]:
    """Errores si algún ID de la curaduría no tiene en ChEBI el nombre que dice el archivo."""
    errors = []
    for node in curation.nodes:
        found = names.get(node.id)
        if found != node.nombre:
            errors.append(f"{node.id} se llama {found!r} en ChEBI, no {node.nombre!r}.")
    return errors


@dataclass(frozen=True)
class Classifier:
    curation: CompoundCuration
    ontology: Mapping[str, frozenset[str]]

    def ontology_class(self, compound: str) -> Clase:
        found = ancestors(compound, self.ontology) | {compound}
        for rule in self.curation.clases:
            if any(node.id in found for node in rule.ancestros):
                return rule.clase
        return "otro"

    def is_cofactor(self, compound: str) -> bool:
        return any(node.id == compound for node in self.curation.cofactores)

    def classify(self, compound: str) -> tuple[Clase, bool]:
        """(clase, es_cofactor). Un cofactor no inorgánico se colorea como `cofactor`."""
        clase = self.ontology_class(compound)
        cofactor = self.is_cofactor(compound)
        if cofactor and clase != "ion_gas":
            clase = "cofactor"
        return clase, cofactor

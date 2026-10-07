"""Reglas de cobertura de la sección 5 de docs/MANUAL.md, sin lectura de archivos.

La especificación ejecutable son los casos de `schema/casos/cobertura.json`: esta
implementación y la de TypeScript (modo en vivo, `web/lib/`) deben pasar los mismos.

Para un paso P y un organismo O, en este orden:

1. P espontáneo -> `espontaneo` (cuenta como presente).
2. Proteína revisada (Swiss-Prot) de O con alguna reacción Rhea de P -> `alta`.
3. Proteína no revisada (TrEMBL) de O con alguna reacción Rhea de P -> `media`.
4. Proteína de O con alguno de los números EC de P -> `baja` (probable; no suma).
5. Nada -> `sin_anotacion`. Nunca "ausente" (regla 7 de CLAUDE.md).

Las reacciones Rhea de las proteínas se comparan por su reacción maestra: UniProt
anota a menudo la dirección fisiológica (LR o RL), y la curaduría usa el ID maestro.
Los números EC se comparan completos y exactos: un EC parcial como `EC:2.7.1.-` no
coincide con ningún paso.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

Estado = Literal["espontaneo", "alta", "media", "baja", "sin_anotacion"]
Clase = Literal["completa", "casi_completa", "parcial", "no_detectada"]

# Estados que cuentan como presentes en el porcentaje de cobertura.
PRESENTES: frozenset[str] = frozenset({"espontaneo", "alta", "media"})

ADVERTENCIA_COMPLEJO = "complejo_verificar_subunidades"


@dataclass(frozen=True)
class Step:
    """Lo que el algoritmo necesita de un paso curado."""

    id: str
    reacciones: tuple[str, ...]
    ec: tuple[str, ...]
    espontaneo: bool = False
    complejo: bool = False

    @classmethod
    def from_curation(cls, paso: Mapping[str, object]) -> Step:
        return cls(
            id=str(paso["id"]),
            reacciones=tuple(paso.get("reacciones", ())),  # type: ignore[arg-type]
            ec=tuple(paso.get("ec", ())),  # type: ignore[arg-type]
            espontaneo=bool(paso.get("espontaneo", False)),
            complejo=bool(paso.get("complejo", False)),
        )


@dataclass(frozen=True)
class Protein:
    """Proteína de un proteoma con sus anotaciones de actividad (CURIE)."""

    accession: str
    revisada: bool
    rhea: frozenset[str] = frozenset()
    ec: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Thresholds:
    completa: float
    casi_completa: float
    parcial: float


@dataclass(frozen=True)
class StepResult:
    estado: Estado
    proteinas: tuple[str, ...]
    advertencias: tuple[str, ...] = ()

    def as_json(self) -> dict[str, object]:
        out: dict[str, object] = {"estado": self.estado, "proteinas": list(self.proteinas)}
        if self.advertencias:
            out["advertencias"] = list(self.advertencias)
        return out


@dataclass(frozen=True)
class PathwayResult:
    cobertura: float
    clase: Clase
    pasos: dict[str, StepResult]


class ProteomeIndex:
    """Proteínas de un organismo indexadas por reacción Rhea maestra y por número EC."""

    def __init__(self, proteins: Iterable[Protein], maestras: Mapping[str, str] | None = None):
        maestras = maestras or {}
        self._by_rhea: dict[str, list[Protein]] = {}
        self._by_ec: dict[str, list[Protein]] = {}
        for protein in proteins:
            for rid in {maestras.get(r, r) for r in protein.rhea}:
                self._by_rhea.setdefault(rid, []).append(protein)
            for ec in protein.ec:
                self._by_ec.setdefault(ec, []).append(protein)

    def with_rhea(self, reacciones: Iterable[str]) -> list[Protein]:
        return [p for r in reacciones for p in self._by_rhea.get(r, ())]

    def with_ec(self, ecs: Iterable[str]) -> list[Protein]:
        return [p for ec in ecs for p in self._by_ec.get(ec, ())]


def _accessions(proteins: Iterable[Protein]) -> tuple[str, ...]:
    return tuple(sorted({p.accession for p in proteins}))


def step_status(step: Step, index: ProteomeIndex) -> StepResult:
    """Estado de evidencia de un paso en un organismo (reglas 1 a 5)."""
    if step.espontaneo:
        return StepResult("espontaneo", ())
    by_rhea = index.with_rhea(step.reacciones)
    reviewed = [p for p in by_rhea if p.revisada]
    if reviewed:
        found: tuple[Estado, list[Protein]] = ("alta", reviewed)
    elif by_rhea:
        found = ("media", by_rhea)
    elif by_ec := index.with_ec(step.ec):
        found = ("baja", by_ec)
    else:
        return StepResult("sin_anotacion", ())
    estado, proteins = found
    warnings = (ADVERTENCIA_COMPLEJO,) if step.complejo else ()
    return StepResult(estado, _accessions(proteins), warnings)


def classify(presentes: int, total: int, umbrales: Thresholds) -> Clase:
    """Clase de cobertura. Compara con enteros para que 4/5 sea exactamente 80 %."""
    if total <= 0:
        raise ValueError("Una vía sin pasos no tiene cobertura.")
    scaled = presentes * 100
    if scaled >= umbrales.completa * total:
        return "completa"
    if scaled >= umbrales.casi_completa * total:
        return "casi_completa"
    if scaled >= umbrales.parcial * total:
        return "parcial"
    return "no_detectada"


def pathway_coverage(
    steps: Sequence[Step], index: ProteomeIndex, umbrales: Thresholds
) -> PathwayResult:
    """Estado de cada paso, porcentaje de pasos presentes o espontáneos y clase."""
    if not steps:
        raise ValueError("Una vía sin pasos no tiene cobertura.")
    results = {step.id: step_status(step, index) for step in steps}
    presentes = sum(1 for r in results.values() if r.estado in PRESENTES)
    return PathwayResult(
        cobertura=round(presentes * 100 / len(steps), 1),
        clase=classify(presentes, len(steps), umbrales),
        pasos=results,
    )

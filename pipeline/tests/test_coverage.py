"""Algoritmo de cobertura contra los casos compartidos de schema/casos/cobertura.json.

Los mismos casos los pasa la implementación TypeScript de web/lib/. Los IDs de los
casos son ficticios: prueban la lógica, no son datos.
"""

import json

import pytest

from metabo.coverage.algorithm import (
    Protein,
    ProteomeIndex,
    Step,
    Thresholds,
    classify,
    pathway_coverage,
)
from metabo.paths import repo_root

CASES_FILE = repo_root() / "schema" / "casos" / "cobertura.json"
SPEC = json.loads(CASES_FILE.read_text(encoding="utf-8"))


def _protein(data: dict) -> Protein:
    return Protein(
        accession=data["accession"],
        revisada=data["revisada"],
        rhea=frozenset(data["rhea"]),
        ec=frozenset(data["ec"]),
    )


@pytest.mark.parametrize("case", SPEC["casos"], ids=lambda c: c["nombre"])
def test_shared_case(case: dict) -> None:
    steps = [Step.from_curation(p) for p in case["pasos"]]
    index = ProteomeIndex((_protein(p) for p in case["proteinas"]), case.get("maestras"))
    umbrales = Thresholds(**case.get("umbrales", SPEC["umbrales"]))

    result = pathway_coverage(steps, index, umbrales)

    assert result.cobertura == case["esperado"]["cobertura"]
    assert result.clase == case["esperado"]["clase"]
    assert {k: v.as_json() for k, v in result.pasos.items()} == case["esperado"]["pasos"]


def test_case_names_are_unique() -> None:
    names = [c["nombre"] for c in SPEC["casos"]]
    assert len(names) == len(set(names))


def test_pathway_without_steps_is_an_error() -> None:
    with pytest.raises(ValueError):
        pathway_coverage([], ProteomeIndex([]), Thresholds(100, 80, 30))


@pytest.mark.parametrize(
    ("presentes", "total", "clase"),
    [
        (10, 10, "completa"),
        (9, 10, "casi_completa"),
        (8, 10, "casi_completa"),
        (7, 10, "parcial"),
        (3, 10, "parcial"),
        (2, 10, "no_detectada"),
        (0, 1, "no_detectada"),
    ],
)
def test_classify_thresholds(presentes: int, total: int, clase: str) -> None:
    assert classify(presentes, total, Thresholds(100, 80, 30)) == clase

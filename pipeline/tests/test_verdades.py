"""Verdades biológicas (sección 14 de docs/MANUAL.md) con los datos reales de raw/.

Necesitan las descargas de Rhea y UniProt (`uv run metabo extraer rhea` y
`uv run metabo extraer uniprot`); sin ellas se omiten. Si una falla, se investiga si
el error está en el algoritmo, en la curaduría o en un cambio real de la anotación:
nunca se ajusta el resultado esperado para que pase (CLAUDE.md).

Solo están las verdades de vías ya curadas en curation/vias/. Las demás de la tabla
de la sección 14 (glioxilato, ciclo de la urea, fermentación alcohólica, Krebs) se
agregan cuando se curen esas vías.
"""

from __future__ import annotations

from datetime import date

import pytest

from metabo import curation
from metabo.config import load_config
from metabo.coverage import compute
from metabo.coverage.algorithm import ProteomeIndex
from metabo.coverage.proteome import read_proteins
from metabo.errors import ConfigError
from metabo.organisms import load_organisms
from metabo.paths import repo_root

# (vía, taxón, clase esperada, referencia bibliográfica).
# TODO: la referencia de cada verdad la aportan Luisa o los revisores científicos;
# las citas nunca se escriben de memoria (regla 6 de CLAUDE.md).
VERDADES = [
    ("glucolisis", "taxon:511145", "completa", "TODO"),  # E. coli K-12 MG1655
    ("glucolisis", "taxon:224308", "completa", "TODO"),  # B. subtilis 168
    ("glucolisis", "taxon:559292", "completa", "TODO"),  # S. cerevisiae S288C
    ("glucolisis", "taxon:9606", "completa", "TODO"),  # Homo sapiens
]


@pytest.fixture(scope="module")
def inputs() -> compute.CoverageInputs:
    raw_dir = repo_root() / load_config().directorios.crudos
    try:
        return compute.CoverageInputs.from_raw(raw_dir, load_organisms())
    except ConfigError as exc:
        pytest.skip(f"Faltan datos descargados en raw/: {exc}")


@pytest.fixture(scope="module")
def indexes(inputs: compute.CoverageInputs) -> dict[str, ProteomeIndex]:
    return {
        taxon: ProteomeIndex(read_proteins(path), inputs.maestras)
        for taxon, path in inputs.proteomas.items()
    }


@pytest.mark.parametrize(("slug", "taxon", "clase", "referencia"), VERDADES)
def test_biological_truth(
    slug: str,
    taxon: str,
    clase: str,
    referencia: str,
    inputs: compute.CoverageInputs,
    indexes: dict[str, ProteomeIndex],
) -> None:
    via = curation.load_via(repo_root() / "curation" / "vias" / f"{slug}.yaml")
    umbrales = compute.thresholds(load_config().cobertura.umbrales)
    document = compute.coverage_document(
        via, taxon, indexes[taxon], umbrales, inputs.versiones, date.today()
    )
    unannotated = {
        k: v["estado"]
        for k, v in document["pasos"].items()
        if v["estado"] not in ("alta", "media", "espontaneo")
    }
    assert document["clase"] == clase, f"{slug} en {taxon}: pasos sin presencia {unannotated}"

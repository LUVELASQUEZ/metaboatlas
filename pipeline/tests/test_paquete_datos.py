"""Paquete de datos completo con los datos reales de raw/.

Necesita las descargas de las cinco fuentes de la fase 0 (`uv run metabo extraer
<fuente>`); sin ellas se omite. Cada documento se valida contra schema/ al armarse.
"""

from datetime import date

import pytest

from metabo import curation
from metabo.config import load_config
from metabo.coverage import compute
from metabo.errors import ConfigError
from metabo.export import compounds, package
from metabo.organisms import load_organisms
from metabo.paths import repo_root


@pytest.fixture(scope="module")
def documents() -> dict:
    root = repo_root()
    config = load_config()
    vias = [curation.load_via(p) for p in sorted((root / "curation" / "vias").glob("*.yaml"))]
    try:
        built = package.build(
            root / config.directorios.crudos,
            vias,
            load_organisms(),
            compounds.load_curation(root / "curation" / "compuestos.yaml"),
            compute.thresholds(config.cobertura.umbrales),
            date.today(),
        )
    except (ConfigError, FileNotFoundError) as exc:
        pytest.skip(f"Faltan datos descargados en raw/: {exc}")
    return built.documents


@pytest.mark.parametrize(
    ("compound", "clase", "es_cofactor"),
    [
        ("CHEBI:4167", "carbohidrato", False),  # D-glucopyranose
        ("CHEBI:59776", "carbohidrato", False),  # D-glyceraldehyde 3-phosphate(2-)
        ("CHEBI:15361", "otro", False),  # pyruvate: ChEBI no lo clasifica como carbohidrato
        ("CHEBI:30616", "cofactor", True),  # ATP(4-)
        ("CHEBI:57540", "cofactor", True),  # NAD(1-)
        ("CHEBI:15378", "ion_gas", True),  # hydron
    ],
)
def test_glycolysis_compound_classes(documents, compound, clase, es_cofactor) -> None:
    document = documents[f"compuestos/{package.file_name(compound)}"]
    assert (document["clase"], document["es_cofactor"]) == (clase, es_cofactor)


def test_every_glycolysis_step_has_its_reactions_and_enzymes(documents) -> None:
    via = documents["vias/glucolisis.json"]
    for step in via["pasos"]:
        for rid in step["reacciones"]:
            assert f"reacciones/{package.file_name(rid)}" in documents
        for ec in step["ec"]:
            assert documents[f"enzimas/{package.file_name(ec)}"]["estado"] == "vigente"

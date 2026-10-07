"""Los organismos de organismos.yaml contra el volcado real de NCBI Taxonomy en raw/.

Necesita `uv run metabo extraer ncbi_taxonomy`; sin esa descarga se omite.
"""

import pytest

from metabo.config import load_config
from metabo.errors import ConfigError
from metabo.manifest import Manifest
from metabo.organisms import load_organisms
from metabo.paths import repo_root
from metabo.sources import ncbi_taxonomy


def test_every_organism_exists_with_its_ncbi_name() -> None:
    raw_dir = repo_root() / load_config().directorios.crudos
    try:
        manifest = Manifest.read(raw_dir / "manifest.json")
        _, files = manifest.latest(ncbi_taxonomy.FUENTE, (ncbi_taxonomy.ARCHIVE,))
    except (ConfigError, FileNotFoundError) as exc:
        pytest.skip(f"Falta el volcado de NCBI Taxonomy en raw/: {exc}")

    organisms = load_organisms()
    records = ncbi_taxonomy.read_taxa(
        raw_dir / files[ncbi_taxonomy.ARCHIVE], [o.id for o in organisms]
    )
    for organism in organisms:
        record = records[organism.id]
        assert record.nombre_cientifico == organism.nombre_ncbi, organism.id
        assert record.dominio is not None, organism.id

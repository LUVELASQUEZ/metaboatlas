"""Lectura de proteomas y cálculo de cobertura desde raw/.

Los archivos de estas pruebas son ficticios (accesiones, IDs Rhea y EC inventados
para probar la lógica); no son datos.
"""

import gzip
import hashlib
import json
from datetime import date
from pathlib import Path

import pytest

from metabo.coverage import compute
from metabo.coverage.algorithm import Protein, Thresholds
from metabo.coverage.proteome import read_proteins
from metabo.errors import ConfigError, SourceFormatError
from metabo.manifest import DownloadRecord, Manifest
from metabo.organisms import Organism

HEADER = "Entry\tProtein names\tReviewed\tEC number\tRhea ID\n"
ROWS = (
    "Z9Z991\tenzima uno\treviewed\t9.9.9.1; 9.9.9.-\tRHEA:1001 RHEA:2000\n"
    "Z9Z992\tenzima dos\tunreviewed\t\t\n"
)
DIRECTIONS = "RHEA_ID_MASTER\tRHEA_ID_LR\tRHEA_ID_RL\tRHEA_ID_BI\n1000\t1001\t1002\t1003\n"
ORGANISM = Organism(
    id="taxon:1",
    nombre="Organismo de prueba",
    intereses=["modelo"],
    proteoma_referencia="UP000000001",
)
VIA = {
    "id": "via:prueba",
    "pasos": [
        {"id": "p01", "reacciones": ["RHEA:1000"], "ec": ["EC:9.9.9.1"], "espontaneo": False},
        {"id": "p02", "reacciones": ["RHEA:5000"], "ec": ["EC:9.9.9.1"], "espontaneo": False},
    ],
}


def _record(raw_dir: Path, fuente: str, version: str, name: str, body: bytes) -> DownloadRecord:
    relative = f"{fuente}/{version}/{name}"
    path = raw_dir / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return DownloadRecord(
        fuente=fuente,
        url=f"https://datos.ejemplo.invalid/{name}",
        version=version,
        fecha_descarga="2026-10-07",
        archivo=relative,
        sha256=hashlib.sha256(body).hexdigest(),
        bytes=len(body),
        licencia="CC BY 4.0",
    )


@pytest.fixture
def raw_dir(tmp_path: Path) -> Path:
    manifest = Manifest(version_datos="2026.10")
    manifest.add(_record(tmp_path, "rhea", "1", "rhea-directions.tsv", DIRECTIONS.encode()))
    body = gzip.compress((HEADER + ROWS).encode("utf-8"))
    manifest.add(_record(tmp_path, "uniprot", "2026_01", "UP000000001.tsv.gz", body))
    manifest.write(tmp_path / "manifest.json")
    return tmp_path


def test_read_proteins_uses_curies(raw_dir: Path) -> None:
    proteins = list(read_proteins(raw_dir / "uniprot/2026_01/UP000000001.tsv.gz"))
    assert proteins == [
        Protein(
            accession="UNIPROT:Z9Z991",
            revisada=True,
            rhea=frozenset({"RHEA:1001", "RHEA:2000"}),
            ec=frozenset({"EC:9.9.9.1", "EC:9.9.9.-"}),
        ),
        Protein(accession="UNIPROT:Z9Z992", revisada=False),
    ]


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("Entry\tReviewed\tRhea ID\nX1\treviewed\t\n", "EC number"),
        (HEADER + "Z9Z991\tn\tquizas\t\t\n", "Reviewed"),
        (HEADER + "Z9Z991\tn\treviewed\t\t1000\n", "RHEA:"),
    ],
)
def test_read_proteins_rejects_unexpected_format(tmp_path: Path, text: str, message: str) -> None:
    path = tmp_path / "UP000000001.tsv.gz"
    path.write_bytes(gzip.compress(text.encode("utf-8")))
    with pytest.raises(SourceFormatError, match=message):
        list(read_proteins(path))


def test_compute_and_write(raw_dir: Path, tmp_path: Path) -> None:
    inputs = compute.CoverageInputs.from_raw(raw_dir, [ORGANISM])
    assert inputs.versiones == {"uniprot": "2026_01", "rhea": "1"}

    documents = compute.compute_all(
        [VIA], [ORGANISM], inputs, Thresholds(100, 80, 30), date(2026, 10, 7)
    )
    assert documents == [
        {
            "via": "via:prueba",
            "taxon": "taxon:1",
            "cobertura": 50.0,
            "clase": "parcial",
            "pasos": {
                # RHEA:1001 es la dirección LR de la maestra RHEA:1000.
                "p01": {"estado": "alta", "proteinas": ["UNIPROT:Z9Z991"]},
                "p02": {"estado": "baja", "proteinas": ["UNIPROT:Z9Z991"]},
            },
            "modo": "precalculado",
            "calculado": "2026-10-07",
            "fuentes": {"uniprot": "2026_01", "rhea": "1"},
        }
    ]

    out = tmp_path / "data" / "2026.10"
    [path] = compute.write_documents(documents, out)
    assert path == out / "cobertura" / "prueba" / "1.json"
    assert json.loads(path.read_text(encoding="utf-8")) == documents[0]


def test_missing_proteome_is_reported(raw_dir: Path) -> None:
    other = ORGANISM.model_copy(update={"id": "taxon:2", "proteoma_referencia": "UP000000002"})
    with pytest.raises(ConfigError, match="UP000000002"):
        compute.CoverageInputs.from_raw(raw_dir, [other])


def test_organism_without_proteome_is_reported(raw_dir: Path) -> None:
    other = ORGANISM.model_copy(update={"proteoma_referencia": None})
    with pytest.raises(ConfigError, match="taxon:1"):
        compute.CoverageInputs.from_raw(raw_dir, [other])

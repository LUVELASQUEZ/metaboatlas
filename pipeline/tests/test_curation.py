"""Verificación de la curaduría de vías.

Los datos de referencia de estas pruebas son ficticios (IDs y EC inventados para
probar la lógica); no se usan como datos. La única excepción es la última prueba,
que revisa la estructura de las vías reales de curation/vias/ sin usar la red.
"""

import copy
import gzip
import hashlib
from pathlib import Path

import pytest

from metabo import curation
from metabo.errors import ConfigError
from metabo.manifest import DownloadRecord, Manifest
from metabo.paths import repo_root
from metabo.sources.enzyme import EnzymeEntry
from metabo.sources.rhea import Participant, Reaction


def reaction(rid: str, *chebi: str) -> Reaction:
    return Reaction(
        id=rid,
        definicion="A = B",
        direccion="=",
        izquierda=(Participant(chebi=(chebi[0],), coeficiente=1),),
        derecha=tuple(Participant(chebi=(c,), coeficiente=1) for c in chebi[1:]),
        ec=(),
    )


def enzyme_entry(ec: str, **kwargs) -> EnzymeEntry:
    values = {"nombre": "enzima ficticia", "eliminada": False, "transferida_a": ()} | kwargs
    return EnzymeEntry(ec=ec, **values)


@pytest.fixture
def data() -> curation.ReferenceData:
    return curation.ReferenceData(
        versiones={"rhea": "1", "enzyme": "2026-01-01", "chebi": "1"},
        reacciones={
            "RHEA:10": reaction("RHEA:10", "CHEBI:1", "CHEBI:2"),
            "RHEA:11": reaction("RHEA:11", "CHEBI:1", "CHEBI:2"),
            "RHEA:20": reaction("RHEA:20", "CHEBI:2", "CHEBI:3"),
            "RHEA:30": reaction("RHEA:30", "CHEBI:3", "CHEBI:99"),
        },
        maestras={"RHEA:10": "RHEA:10", "RHEA:11": "RHEA:10", "RHEA:20": "RHEA:20"},
        rhea2ec={
            "RHEA:10": frozenset({"EC:7.1.1.1"}),
            "RHEA:20": frozenset({"EC:7.1.1.2"}),
            "RHEA:30": frozenset({"EC:7.1.1.1"}),
        },
        enzimas={
            "EC:7.1.1.1": enzyme_entry("EC:7.1.1.1"),
            "EC:7.1.1.2": enzyme_entry("EC:7.1.1.2"),
            "EC:7.1.1.3": enzyme_entry("EC:7.1.1.3", eliminada=True),
            "EC:7.1.1.4": enzyme_entry("EC:7.1.1.4", transferida_a=("EC:7.1.1.2",)),
        },
        compuestos={"CHEBI:1": "uno", "CHEBI:2": "dos", "CHEBI:3": "tres"},
    )


VIA = {
    "id": "via:ejemplo",
    "nombre": {"es": "Vía de ejemplo", "en": "Example pathway"},
    "categoria": "cat:carbohidratos",
    "compartimento": ["citosol"],
    "modulos": [{"id": "m1", "nombre": "Módulo", "pasos": ["p01", "p02"]}],
    "pasos": [
        {
            "id": "p01",
            "orden": 1,
            "titulo": "Paso uno",
            "reacciones": ["RHEA:10"],
            "ec": ["EC:7.1.1.1"],
            "espontaneo": False,
            "regulacion": True,
        },
        {
            "id": "p02",
            "orden": 2,
            "titulo": "Paso dos",
            "reacciones": ["RHEA:20"],
            "ec": ["EC:7.1.1.2"],
            "espontaneo": False,
            "regulacion": False,
        },
    ],
    "conecta_con": [],
    "variante_de": None,
    "xrefs": [],
    "version": "2026.10",
    "estado_editorial": "borrador",
    "fuentes": {"rhea": "1", "enzyme": "2026-01-01", "chebi": "1"},
}


def via(**step_changes) -> dict:
    """Copia de VIA con cambios en el paso p01."""
    result = copy.deepcopy(VIA)
    result["pasos"][0].update(step_changes)
    return result


def test_valid_via_has_no_errors(data):
    assert curation.check_via(via(), data) == []


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"reacciones": ["RHEA:99"]}, "RHEA:99 no existe en Rhea"),
        ({"reacciones": ["RHEA:11"]}, "RHEA:11 no es una reacción maestra; usa RHEA:10"),
        ({"reacciones": ["RHEA:20"]}, "RHEA:20 no está asociado en rhea2ec a ningún EC del paso"),
        ({"reacciones": ["RHEA:30"]}, "CHEBI:99 (participante de RHEA:30) no existe en ChEBI"),
        ({"ec": ["EC:7.1.1.1", "EC:7.9.9.9"]}, "EC:7.9.9.9 no existe en enzyme.dat"),
        ({"ec": ["EC:7.1.1.1", "EC:7.1.1.3"]}, "EC:7.1.1.3 está eliminado"),
        ({"ec": ["EC:7.1.1.1", "EC:7.1.1.4"]}, "EC:7.1.1.4 fue transferido en ENZYME a EC:7.1.1.2"),
    ],
)
def test_each_id_is_checked_against_the_data(data, changes, message):
    errors = curation.check_via(via(**changes), data)
    assert any(message in e for e in errors), errors


def test_source_versions_must_match_the_downloaded_ones(data):
    changed = via()
    changed["fuentes"]["rhea"] = "0"
    errors = curation.check_via(changed, data)
    assert errors == [
        "fuentes.rhea: la vía dice '0' y la versión descargada es '1'; "
        "vuelve a verificar la vía y actualiza la versión."
    ]


@pytest.mark.parametrize(
    "mutate, message",
    [
        (
            lambda v: v["modulos"][0]["pasos"].remove("p02"),
            "p02: debe estar en exactamente un módulo",
        ),
        (lambda v: v["modulos"][0]["pasos"].append("p03"), "p03: aparece en un módulo"),
        (lambda v: v["pasos"][1].update(orden=3), "`orden` de los pasos"),
        (lambda v: v["pasos"][1].update(id="p01"), "p01: el ID de paso está repetido"),
        (lambda v: v["pasos"][0].update(reacciones=["10"]), "esquema:"),
        (lambda v: v.pop("fuentes"), "esquema:"),
    ],
)
def test_structure_errors(mutate, message):
    changed = copy.deepcopy(VIA)
    mutate(changed)
    errors = curation.check_structure(changed)
    assert any(message in e for e in errors), errors


def test_search_ec_lists_master_reactions_in_numeric_order(data):
    found = curation.search_ec(data, "EC:7.1.1.1")
    assert [r.id for r in found] == ["RHEA:10", "RHEA:30"]
    assert curation.search_ec(data, "EC:7.9.9.9") == []


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


def test_reference_data_is_read_from_the_manifest(tmp_path):
    raw_dir = tmp_path / "raw"
    reactions = (
        "ENTRY       RHEA:10\nDEFINITION  A = B\nEQUATION    CHEBI:1 = CHEBI:2\n"
        "ENZYME      7.1.1.1\n///\n"
    )
    compounds_header = (
        "id\tname\tstatus_id\tsource\tparent_id\tmerge_type\tchebi_accession\tdefinition\t"
        "ascii_name\tstars\tmodified_on\trelease_date\n"
    )
    compounds = compounds_header + "1\tuno\t0\t0\t0\t0\tCHEBI:1\t0\t0\t3\t0\t0\n"
    records = [
        _record(raw_dir, "rhea", "1", "rhea-reactions.txt.gz", gzip.compress(reactions.encode())),
        _record(
            raw_dir,
            "rhea",
            "1",
            "rhea-directions.tsv",
            b"RHEA_ID_MASTER\tRHEA_ID_LR\tRHEA_ID_RL\tRHEA_ID_BI\n10\t11\t12\t13\n",
        ),
        _record(
            raw_dir,
            "rhea",
            "1",
            "rhea2ec.tsv",
            b"RHEA_ID\tDIRECTION\tMASTER_ID\tID\n10\tUN\t10\t7.1.1.1\n",
        ),
        _record(
            raw_dir,
            "enzyme",
            "2026-01-01",
            "enzyme.dat",
            b"ID   7.1.1.1\nDE   enzima ficticia.\n//\n",
        ),
        _record(raw_dir, "chebi", "1", "compounds.tsv.gz", gzip.compress(compounds.encode())),
    ]
    manifest = Manifest(version_datos="2026.10")
    for record in records:
        manifest.add(record)
    manifest.write(raw_dir / "manifest.json")

    data = curation.ReferenceData.from_raw(raw_dir)
    assert data.versiones == {"rhea": "1", "enzyme": "2026-01-01", "chebi": "1"}
    assert data.maestras["RHEA:12"] == "RHEA:10"
    assert data.rhea2ec == {"RHEA:10": {"EC:7.1.1.1"}}
    assert data.enzimas["EC:7.1.1.1"].vigente
    assert data.compuestos == {"CHEBI:1": "uno"}
    assert [r.id for r in curation.search_ec(data, "EC:7.1.1.1")] == ["RHEA:10"]


def test_missing_downloads_are_reported(tmp_path):
    with pytest.raises(ConfigError, match="metabo extraer"):
        curation.ReferenceData.from_raw(tmp_path)
    Manifest(version_datos="2026.10").write(tmp_path / "manifest.json")
    with pytest.raises(ConfigError, match="metabo extraer rhea"):
        curation.ReferenceData.from_raw(tmp_path)


CURATED = sorted((repo_root() / "curation" / "vias").glob("*.yaml"))


@pytest.mark.parametrize("path", CURATED, ids=[p.name for p in CURATED])
def test_curated_pathways_have_a_valid_structure(path):
    """No necesita raw/: la verificación de IDs se hace con `metabo curar validar`."""
    assert curation.check_structure(curation.load_via(path)) == []

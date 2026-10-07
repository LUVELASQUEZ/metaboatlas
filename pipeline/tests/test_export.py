"""Exportación del paquete de datos con un raw/ ficticio: ninguna prueba usa la red.

Los archivos imitan el formato de cada fuente. Sus IDs, nombres, fórmulas y
proteínas son ficticios (prueban la lógica, no son datos) y nunca deben copiarse a
curation/ ni al paquete de datos.
"""

import gzip
import hashlib
import io
import json
import tarfile
from datetime import date
from pathlib import Path

import pytest

from metabo import schemas
from metabo.coverage.algorithm import Thresholds
from metabo.errors import ConfigError
from metabo.export import compounds as export_compounds
from metabo.export import package
from metabo.manifest import DownloadRecord, Manifest
from metabo.organisms import Organism
from metabo.sources import chebi, enzyme, uniprot

# --- Vía y curaduría ficticias -------------------------------------------------

VIA = {
    "id": "via:prueba",
    "nombre": {"es": "Vía de prueba", "en": "Test pathway"},
    "categoria": "cat:carbohidratos",
    "compartimento": ["citosol"],
    "modulos": [{"id": "m1", "nombre": "Módulo de prueba", "pasos": ["p01", "p02"]}],
    "pasos": [
        {
            "id": "p01",
            "orden": 1,
            "titulo": "Paso uno",
            "reacciones": ["RHEA:1000"],
            "ec": ["EC:7.99.99.1"],
            "espontaneo": False,
            "regulacion": True,
        },
        {
            "id": "p02",
            "orden": 2,
            "titulo": "Paso dos",
            "reacciones": ["RHEA:2000"],
            "ec": ["EC:7.99.99.2"],
            "espontaneo": False,
            "regulacion": False,
        },
    ],
    "conecta_con": [],
    "variante_de": None,
    "xrefs": [],
    "version": "2026.10",
    "estado_editorial": "borrador",
    "fuentes": {"rhea": "1"},
}

CURATION = export_compounds.CompoundCuration.model_validate(
    {
        "clases": [
            {"clase": "nucleotido", "ancestros": [{"id": "CHEBI:900", "nombre": "nucleótido"}]},
            {"clase": "carbohidrato", "ancestros": [{"id": "CHEBI:901", "nombre": "azúcar"}]},
            {"clase": "ion_gas", "ancestros": [{"id": "CHEBI:902", "nombre": "inorgánico"}]},
        ],
        "cofactores": [
            {"id": "CHEBI:3", "nombre": "moneda(2-)"},
            {"id": "CHEBI:4", "nombre": "protón"},
        ],
    }
)

ORGANISMS = [
    Organism(
        id="taxon:13",
        nombre="Bacteria de prueba",
        intereses=["modelo"],
        proteoma_referencia="UP000000001",
    ),
    Organism(
        id="taxon:14",
        nombre="Levadura de prueba",
        intereses=["industrial"],
        proteoma_referencia="UP000000002",
    ),
]

# --- Archivos crudos ficticios --------------------------------------------------


def tsv(*rows: tuple[str, ...]) -> bytes:
    return "".join("\t".join(row) + "\n" for row in rows).encode("utf-8")


def gz(body: bytes) -> bytes:
    return gzip.compress(body)


def dmp(*rows: tuple[str, ...]) -> bytes:
    return "".join("\t|\t".join(row) + "\t|\n" for row in rows).encode("utf-8")


def tar_gz(members: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for name, body in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(body)
            tar.addfile(info, io.BytesIO(body))
    return buffer.getvalue()


REACTIONS = b"""ENTRY       RHEA:1000
DEFINITION  <i>sugar</i> + moneda = sugar phosphate + H(+)
EQUATION    CHEBI:1 + CHEBI:3 = CHEBI:2 + CHEBI:4
ENZYME      7.99.99.1
///
ENTRY       RHEA:2000
DEFINITION  sugar(out) = sugar(in)
EQUATION    CHEBI:1 = CHEBI:1
ENZYME      7.99.99.2
///
"""

COMPOUNDS = tsv(
    chebi.TSV_FILES["compounds.tsv.gz"],
    *[
        (n, name, "1", "ChEBI", "", "", f"CHEBI:{n}", definition, name, "3", "", "")
        for n, name, definition in [
            ("1", "<small>D</small>-azúcar", "Un azúcar ficticio."),
            ("2", "azúcar fosfato(2-)", ""),
            ("3", "moneda(2-)", "Una moneda ficticia."),
            ("4", "protón", ""),
            ("900", "nucleótido", ""),
            ("901", "azúcar", ""),
            ("902", "inorgánico", ""),
        ]
    ],
)
CHEMICAL = tsv(
    chebi.TSV_FILES["chemical_data.tsv.gz"],
    ("20", "1", "C6H12O6", "0", "180.1", "180.06339", "1", "1", "true"),
    ("10", "1", "C6H12O6", "0", "180.1", "180.06000", "1", "1", "true"),
    ("30", "4", "H", "1", "1.0", "1.00728", "1", "1", "true"),
)
NAMES = tsv(
    chebi.TSV_FILES["names.tsv.gz"],
    ("1", "1", "<i>D</i>-azúcar ficticio", "SYNONYM", "1", "false", "en", "D-azucar"),
    ("2", "1", "<small>D</small>-azúcar", "IUPAC NAME", "1", "false", "en", "D-azucar"),
    ("3", "1", "marca registrada", "BRAND NAME", "1", "false", "en", "marca"),
)
RELATION_TYPE = tsv(
    chebi.TSV_FILES["relation_type.tsv.gz"],
    ("4", "has_role", "false", "has role"),
    ("5", "is_a", "false", "is a"),
    ("6", "is_conjugate_acid_of", "true", "is conjugate acid of"),
    ("7", "is_conjugate_base_of", "true", "is conjugate base of"),
)
RELATION = tsv(
    chebi.TSV_FILES["relation.tsv.gz"],
    ("1", "5", "1", "901", "1", "", ""),  # azúcar is_a azúcar
    ("2", "7", "2", "1", "1", "", ""),  # azúcar fosfato es base conjugada de 1
    ("3", "5", "3", "900", "1", "", ""),  # moneda is_a nucleótido
    ("4", "5", "4", "902", "1", "", ""),  # protón is_a inorgánico
    ("5", "4", "1", "900", "1", "", ""),  # has_role: no se sigue
)
ENZYME_DAT = b"""CC   Release of 02-Sep-2026
//
ID   7.99.99.1
DE   enzima ficticia uno.
AN   nombre alternativo muy
AN   largo.
AN   otro-
AN   nombre.
CA   sugar + moneda = sugar
CA   phosphate + H(+).
//
ID   7.99.99.2
DE   enzima ficticia dos.
//
"""
TAXDUMP = {
    "delnodes.dmp": dmp(("900",)),
    "merged.dmp": dmp(("800", "13")),
    "names.dmp": dmp(
        ("10", "cellular organisms", "", "scientific name"),
        ("11", "Bacteria", "", "scientific name"),
        ("12", "Eukaryota", "", "scientific name"),
        ("13", "Bacteria ficticia", "", "scientific name"),
        ("14", "Levadura ficticia", "", "scientific name"),
        ("14", "fake yeast", "", "genbank common name"),
    ),
    "nodes.dmp": dmp(
        ("10", "1", "cellular root"),
        ("11", "10", "domain"),
        ("12", "10", "domain"),
        ("13", "11", "species"),
        ("14", "12", "species"),
    ),
    "taxidlineage.dmp": dmp(("13", "10 11"), ("14", "10 12")),
}


def proteome(*rows: dict[str, str]) -> bytes:
    header = tuple(uniprot.FIELDS.values())
    return gz(tsv(header, *[tuple(row.get(h, "") for h in header) for row in rows]))


PROTEOMES = {
    "UP000000001": proteome(
        {
            "Entry": "Z9Z991",
            "Protein names": "Enzima uno",
            "Gene Names": "enzA b0001",
            "EC number": "7.99.99.1",
            "Rhea ID": "RHEA:1001",
            "Reviewed": "reviewed",
            "Annotation": "5.0",
            "KEGG": "zzz:b0001;yyy:B1;",
        },
        {
            "Entry": "Z9Z992",
            "Reviewed": "unreviewed",
            "Annotation": "1.0",
            "KEGG": "zzz:b0002;",
        },
    ),
    "UP000000002": proteome(
        {
            "Entry": "Z9Z993",
            "Protein names": "Enzima dos",
            "EC number": "7.99.99.2",
            "Reviewed": "unreviewed",
            "Annotation": "2.0",
        },
    ),
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
    raw = tmp_path / "raw"
    files = {
        ("rhea", "1"): {
            "rhea-directions.tsv": tsv(
                ("RHEA_ID_MASTER", "RHEA_ID_LR", "RHEA_ID_RL", "RHEA_ID_BI"),
                ("1000", "1001", "1002", "1003"),
                ("2000", "2001", "2002", "2003"),
            ),
            "rhea2ec.tsv": tsv(
                ("RHEA_ID", "DIRECTION", "MASTER_ID", "ID"),
                ("1000", "UN", "1000", "7.99.99.1"),
                ("2000", "UN", "2000", "7.99.99.2"),
                ("3000", "UN", "3000", "7.99.99.1"),
            ),
            "rhea-reactions.txt.gz": gz(REACTIONS),
        },
        ("chebi", "1"): {
            "compounds.tsv.gz": gz(COMPOUNDS),
            "chemical_data.tsv.gz": gz(CHEMICAL),
            "names.tsv.gz": gz(NAMES),
            "relation.tsv.gz": gz(RELATION),
            "relation_type.tsv.gz": gz(RELATION_TYPE),
        },
        ("enzyme", "2026-09-02"): {"enzyme.dat": ENZYME_DAT},
        ("ncbi_taxonomy", "2026-10-07"): {"new_taxdump.tar.gz": tar_gz(TAXDUMP)},
        ("uniprot", "2026_01"): {f"{up}.tsv.gz": body for up, body in PROTEOMES.items()},
    }
    manifest = Manifest(version_datos="2026.10")
    for (fuente, version), bodies in files.items():
        for name, body in bodies.items():
            manifest.add(_record(raw, fuente, version, name, body))
    manifest.write(raw / "manifest.json")
    return raw


def build(raw_dir: Path, curation=CURATION) -> package.Package:
    return package.build(
        raw_dir, [VIA], ORGANISMS, curation, Thresholds(100, 80, 30), date(2026, 10, 7)
    )


# --- Pruebas --------------------------------------------------------------------


def test_package_has_every_entity_and_validates(raw_dir):
    built = build(raw_dir)
    assert sorted(built.documents) == [
        "cobertura/prueba/13.json",
        "cobertura/prueba/14.json",
        "compuestos/CHEBI_1.json",
        "compuestos/CHEBI_2.json",
        "compuestos/CHEBI_3.json",
        "compuestos/CHEBI_4.json",
        "enzimas/EC_7.99.99.1.json",
        "enzimas/EC_7.99.99.2.json",
        "organismos/13.json",
        "organismos/14.json",
        "reacciones/RHEA_1000.json",
        "reacciones/RHEA_2000.json",
        "vias/prueba.json",
    ]
    assert {d.fuente for d in built.manifest.descargas} == {
        "rhea",
        "chebi",
        "enzyme",
        "ncbi_taxonomy",
        "uniprot",
    }


def test_compounds_follow_the_ontology_and_the_cofactor_list(raw_dir):
    docs = build(raw_dir).documents
    sugar = docs["compuestos/CHEBI_1.json"]
    assert sugar["nombre"] == {"es": None, "en": "D-azúcar"}
    assert sugar["sinonimos"] == ["D-azúcar ficticio"]  # sin el nombre ni BRAND NAME
    assert sugar["masa_monoisotopica"] == 180.06  # fila de chemical_data con menor id
    assert (sugar["clase"], sugar["es_cofactor"]) == ("carbohidrato", False)
    # Base conjugada de un azúcar: hereda la clase.
    assert docs["compuestos/CHEBI_2.json"]["clase"] == "carbohidrato"
    # Cofactor orgánico: clase cofactor. Cofactor inorgánico: conserva ion_gas.
    assert (
        docs["compuestos/CHEBI_3.json"]["clase"],
        docs["compuestos/CHEBI_3.json"]["es_cofactor"],
    ) == ("cofactor", True)
    assert (
        docs["compuestos/CHEBI_4.json"]["clase"],
        docs["compuestos/CHEBI_4.json"]["es_cofactor"],
    ) == ("ion_gas", True)
    assert docs["compuestos/CHEBI_2.json"]["formula"] is None
    assert docs["compuestos/CHEBI_4.json"]["carga"] == 1


def test_reactions_keep_rhea_data(raw_dir):
    docs = build(raw_dir).documents
    first = docs["reacciones/RHEA_1000.json"]
    assert first["direcciones"] == {
        "izquierda_a_derecha": "RHEA:1001",
        "derecha_a_izquierda": "RHEA:1002",
        "bidireccional": "RHEA:1003",
    }
    assert first["participantes"][0] == {
        "compuesto": "CHEBI:1",
        "lado": "izquierda",
        "estequiometria": 1,
    }
    assert first["es_transporte"] is False
    assert first["reversible"] is None
    assert first["procedencia"] == [
        {"fuente": "rhea", "id": "1000", "version": "1", "fecha_descarga": "2026-10-07"}
    ]
    assert docs["reacciones/RHEA_2000.json"]["es_transporte"] is True


def test_enzymes_list_reactions_and_proteins_of_each_organism(raw_dir):
    docs = build(raw_dir).documents
    first = docs["enzimas/EC_7.99.99.1.json"]
    assert first["nombres_alternativos"] == ["nombre alternativo muy largo", "otro-nombre"]
    assert first["reaccion"] == "sugar + moneda = sugar phosphate + H(+)"
    assert first["reacciones"] == ["RHEA:1000", "RHEA:3000"]
    assert first["clase"] == 7
    [protein] = first["proteinas"]
    assert protein["id"] == "UNIPROT:Z9Z991"
    assert protein["taxon"] == "taxon:13"
    assert protein["genes"] == ["enzA", "b0001"]
    assert protein["puntaje_anotacion"] == 5
    assert protein["rhea"] == ["RHEA:1001"]
    [other] = docs["enzimas/EC_7.99.99.2.json"]["proteinas"]
    assert (other["taxon"], other["revisada"]) == ("taxon:14", False)


def test_organisms_combine_ncbi_and_uniprot(raw_dir):
    docs = build(raw_dir).documents
    bacterium = docs["organismos/13.json"]
    assert bacterium["linaje"] == [
        {"taxon": "taxon:10", "nombre": "cellular organisms", "rango": "cellular root"},
        {"taxon": "taxon:11", "nombre": "Bacteria", "rango": "domain"},
    ]
    assert (bacterium["dominio"], bacterium["gram"]) == ("bacteria", None)
    assert bacterium["codigo_kegg"] == "zzz"  # el prefijo más frecuente
    assert bacterium["nombre_comun"] is None
    yeast = docs["organismos/14.json"]
    assert (yeast["dominio"], yeast["gram"], yeast["codigo_kegg"]) == (
        "eucariota",
        "no_aplica",
        None,
    )
    assert yeast["nombre_comun"] == {"es": None, "en": "fake yeast"}
    assert [p["fuente"] for p in yeast["procedencia"]] == ["ncbi_taxonomy", "uniprot"]


def test_coverage_is_part_of_the_package(raw_dir):
    docs = build(raw_dir).documents
    assert docs["cobertura/prueba/13.json"]["pasos"]["p01"]["estado"] == "alta"
    assert docs["cobertura/prueba/14.json"]["pasos"]["p02"]["estado"] == "baja"


def test_curation_names_must_match_chebi(raw_dir):
    wrong = CURATION.model_copy(
        update={"cofactores": [export_compounds.Node(id="CHEBI:3", nombre="ATP")]}
    )
    with pytest.raises(ConfigError, match="CHEBI:3 se llama 'moneda"):
        build(raw_dir, wrong)


def test_write_replaces_the_previous_export(raw_dir, tmp_path):
    out = tmp_path / "data" / "2026.10"
    (out / "viejo").mkdir(parents=True)
    (out / "viejo" / "archivo.json").write_text("{}")
    written = build(raw_dir).write(out)
    assert not (out / "viejo").exists()
    assert out / "manifest.json" in written
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert schemas.validation_errors("manifiesto", manifest) == []
    assert json.loads((out / "vias" / "prueba.json").read_text(encoding="utf-8")) == VIA


def test_enzyme_cofactor_lines_are_split():
    entry = enzyme.parse_entries(
        "ID   7.99.99.3\nDE   ficticia.\nCF   Mg(2+); Mn(2+)\nCF   ; Zn(2+).\n//\n"
    )
    assert entry["EC:7.99.99.3"].cofactores == ("Mg(2+)", "Mn(2+)", "Zn(2+)")


def test_real_compound_curation_is_valid():
    curation = export_compounds.load_curation(
        Path(__file__).parents[2] / "curation" / "compuestos.yaml"
    )
    assert curation.clases[0].clase == "nucleotido"

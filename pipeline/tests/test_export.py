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
from metabo.export import names, package
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


# El nodo CHEBI:901 (azúcar) es más general que el participante CHEBI:1 de Rhea.
MAPA = {
    "via": "via:prueba",
    "lienzo": {"ancho": 300, "alto": 300},
    "compuestos": [
        {"compuesto": "CHEBI:901", "x": 100, "y": 50},
        {"compuesto": "CHEBI:2", "x": 100, "y": 250},
    ],
    "pasos": [
        {
            "paso": "p01",
            "desde": ["CHEBI:901"],
            "hacia": ["CHEBI:2"],
            "rotulo": {"x": 100, "y": 150},
            "cofactores": "derecha",
        },
        {
            "paso": "p02",
            "desde": ["CHEBI:901"],
            "hacia": ["CHEBI:901"],
            "rotulo": {"x": 200, "y": 50},
            "cofactores": "arriba",
        },
    ],
    "modulos": [{"modulo": "m1", "x": 10, "y": 10, "ancho": 280, "alto": 280}],
    "portales": [],
}


def build(raw_dir: Path, curation=CURATION, mapas=None) -> package.Package:
    return package.build(
        raw_dir,
        [VIA],
        ORGANISMS,
        curation,
        Thresholds(100, 80, 30),
        date(2026, 10, 7),
        mapas,
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


def test_maps_are_checked_and_exported(raw_dir):
    docs = build(raw_dir, mapas={"prueba": MAPA}).documents
    assert docs["mapas/prueba.json"] == MAPA
    # Los nodos del mapa también se exportan como compuestos.
    assert docs["compuestos/CHEBI_901.json"]["nombre"]["en"] == "azúcar"


def test_incoherent_map_stops_the_export(raw_dir):
    mapa = json.loads(json.dumps(MAPA))
    mapa["pasos"][0]["desde"] = ["CHEBI:2"]  # 2 solo está a la derecha de RHEA:1000
    with pytest.raises(ConfigError, match=r"curation/mapas/prueba\.json no es coherente"):
        build(raw_dir, mapas={"prueba": mapa})


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


# --- Nombres en español -----------------------------------------------------------


def sparql(*rows: tuple[str, str, str | None]) -> bytes:
    """Respuesta SPARQL JSON ficticia: (ID sin prefijo, QID, etiqueta en español)."""
    bindings = []
    for native, qid, es in rows:
        row = {
            "id": {"type": "literal", "value": native},
            "item": {"type": "uri", "value": f"http://www.wikidata.org/entity/{qid}"},
        }
        if es is not None:
            row["es"] = {"xml:lang": "es", "type": "literal", "value": es}
        bindings.append(row)
    data = {"head": {"vars": ["id", "item", "es"]}, "results": {"bindings": bindings}}
    return json.dumps(data).encode()


def with_wikidata(raw_dir: Path) -> Path:
    manifest = Manifest.read(raw_dir / "manifest.json")
    compounds = sparql(("2", "Q2", "azúcar fosfato"), ("3", "Q3", "moneda"))
    enzymes = sparql(
        ("7.99.99.1", "Q10", "enzima uno"),
        ("7.99.99.2", "Q20", "enzima dos"),
        ("7.99.99.2", "Q21", "otra enzima"),  # dos etiquetas distintas: ambigua
    )
    for name, body in (("compuestos-001.json", compounds), ("enzimas-001.json", enzymes)):
        manifest.add(_record(raw_dir, "wikidata", "2026-10-08", name, body))
    manifest.write(raw_dir / "manifest.json")
    return raw_dir


NOMBRES = names.NameCuration(
    {
        "compuestos": {"CHEBI:3": names.CuratedName(en="moneda(2-)", es="moneda curada")},
        "organismos": {"taxon:14": names.CuratedName(en="fake yeast", es="levadura ficticia")},
    }
)


def build_named(raw_dir: Path, nombres=NOMBRES) -> package.Package:
    return package.build(
        raw_dir,
        [VIA],
        ORGANISMS,
        CURATION,
        Thresholds(100, 80, 30),
        date(2026, 10, 7),
        None,
        nombres,
    )


def test_spanish_names_come_from_curation_then_wikidata(raw_dir):
    built = build_named(with_wikidata(raw_dir))
    docs = built.documents
    curated = docs["compuestos/CHEBI_3.json"]
    assert (curated["nombre"]["es"], curated["nombre_es_origen"]) == ("moneda curada", "curaduria")
    # La curaduría gana sobre Wikidata y no agrega su procedencia.
    assert [p["fuente"] for p in curated["procedencia"]] == ["chebi"]

    from_wikidata = docs["compuestos/CHEBI_2.json"]
    assert from_wikidata["nombre"] == {"es": "azúcar fosfato", "en": "azúcar fosfato(2-)"}
    assert from_wikidata["nombre_es_origen"] == "wikidata"
    assert {"fuente": "wikidata", "tipo": "elemento", "id": "Q2"} in from_wikidata["xrefs"]
    assert from_wikidata["procedencia"][-1] == {
        "fuente": "wikidata",
        "id": "Q2",
        "version": "2026-10-08",
        "fecha_descarga": "2026-10-07",
    }

    missing = docs["compuestos/CHEBI_4.json"]
    assert (missing["nombre"]["es"], missing["nombre_es_origen"]) == (None, None)

    assert docs["enzimas/EC_7.99.99.1.json"]["nombre"]["es"] == "enzima uno"
    # Un EC con dos etiquetas distintas en Wikidata es ambiguo: queda sin nombre.
    assert docs["enzimas/EC_7.99.99.2.json"]["nombre"]["es"] is None

    assert docs["organismos/14.json"]["nombre_comun"] == {
        "es": "levadura ficticia",
        "en": "fake yeast",
    }
    assert "wikidata" in {d.fuente for d in built.manifest.descargas}


def test_wikidata_is_optional_and_left_out_when_unused(raw_dir):
    built = build_named(raw_dir, names.NameCuration())
    assert "wikidata" not in {d.fuente for d in built.manifest.descargas}
    assert built.documents["compuestos/CHEBI_2.json"]["nombre"]["es"] is None


def test_curated_spanish_names_must_match_the_source(raw_dir):
    wrong = names.NameCuration(
        {"enzimas": {"EC:7.99.99.1": names.CuratedName(en="otra cosa", es="algo")}}
    )
    with pytest.raises(ConfigError, match=r"EC:7\.99\.99\.1: el nombre curado es 'otra cosa'"):
        build_named(raw_dir, wrong)


def test_entity_ids_cover_reactions_maps_and_steps(raw_dir):
    compounds, ecs = package.entity_ids(raw_dir, [VIA], {"prueba": MAPA})
    assert compounds == {"CHEBI:1", "CHEBI:2", "CHEBI:3", "CHEBI:4", "CHEBI:901"}
    assert ecs == {"EC:7.99.99.1", "EC:7.99.99.2"}


def test_real_spanish_name_curation_is_valid():
    curation = names.load_curation(Path(__file__).parents[2] / "curation" / "nombres_es.yaml")
    assert curation.get("compuestos", "CHEBI:15361") == names.CuratedName(
        en="pyruvate", es="piruvato"
    )
    assert curation.get("organismos", "taxon:9606") is not None

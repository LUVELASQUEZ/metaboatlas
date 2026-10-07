"""Extractor de Rhea con un servidor simulado: ninguna prueba usa la red.

Las filas de muestra solo imitan el formato de los TSV; sus IDs son ficticios y no
se usan como datos.
"""

import gzip
from datetime import date

import pytest
from conftest import FakeFtp

from metabo.errors import SourceFormatError
from metabo.manifest import Manifest
from metabo.sources import rhea

RELEASE = b"rhea.release.number=142\nrhea.release.date=2026-09-02\n"
DIRECTIONS = b"RHEA_ID_MASTER\tRHEA_ID_LR\tRHEA_ID_RL\tRHEA_ID_BI\n10\t11\t12\t13\n"
EC = b"RHEA_ID\tDIRECTION\tMASTER_ID\tID\n10\tUN\t10\t9.9.9.9\n"
REACTIONS_TEXT = """ENTRY       RHEA:10
DEFINITION  compuesto A + 2 compuesto B = polimero C + H(+)
EQUATION    CHEBI:1 + 2 CHEBI:2 = CHEBI:3,CHEBI:3 + CHEBI:4
ENZYME      7.99.99.9         7.99.99.8         7.99.99.7         7.99.99.6
            7.99.99.5
///
ENTRY       RHEA:11
DEFINITION  compuesto A + 2 compuesto B => polimero C + H(+)
EQUATION    CHEBI:1 + 2 CHEBI:2 => CHEBI:3,CHEBI:3 + CHEBI:4
///
ENTRY       RHEA:13
DEFINITION  compuesto A + 2 compuesto B <=> polimero C + H(+)
EQUATION    CHEBI:1 + 2 CHEBI:2 <=> CHEBI:3,CHEBI:3 + CHEBI:4
///
"""
REACTIONS = gzip.compress(REACTIONS_TEXT.encode())


def files(**overrides: bytes) -> dict[str, bytes]:
    served = {
        rhea.RELEASE_URL: RELEASE,
        f"{rhea.BASE_URL}/tsv/rhea-directions.tsv": DIRECTIONS,
        f"{rhea.BASE_URL}/tsv/rhea2ec.tsv": EC,
        rhea.REACTIONS_URL: REACTIONS,
    }
    for name, body in overrides.items():
        if name == "release":
            url = rhea.RELEASE_URL
        elif name == "reactions":
            url = rhea.REACTIONS_URL
        else:
            url = f"{rhea.BASE_URL}/tsv/{name}"
        served[url] = body
    return served


def test_parse_release():
    assert rhea.parse_release(RELEASE.decode()) == rhea.Release(numero="142", fecha="2026-09-02")


@pytest.mark.parametrize(
    "text",
    [
        "rhea.release.date=2026-09-02\n",
        "rhea.release.number=142\n",
        "rhea.release.number=ciento\nrhea.release.date=2026-09-02\n",
        "rhea.release.number=142\nrhea.release.date=02/09/2026\n",
    ],
)
def test_parse_release_rejects_missing_or_malformed_values(text):
    with pytest.raises(SourceFormatError):
        rhea.parse_release(text)


def test_extract_downloads_into_release_folder(run_extractor, tmp_path):
    raw_dir, (release, records) = run_extractor(rhea.extract, FakeFtp(files()))

    assert release.numero == "142"
    assert [r.archivo for r in records] == [
        "rhea/142/rhea-release.properties",
        "rhea/142/rhea-directions.tsv",
        "rhea/142/rhea2ec.tsv",
        "rhea/142/rhea-reactions.txt.gz",
    ]
    assert (raw_dir / "rhea/142/rhea2ec.tsv").read_bytes() == EC
    assert all(r.version == "142" and r.licencia == "CC BY 4.0" for r in records)


def test_records_validate_against_manifest_schema(run_extractor, tmp_path):
    _, (_, records) = run_extractor(rhea.extract, FakeFtp(files()))
    manifest = Manifest(version_datos="2026.10")
    for record in records:
        manifest.add(record)
    # write() y read() validan contra schema/manifiesto.schema.json.
    manifest.write(tmp_path / "manifest.json")
    saved = Manifest.read(tmp_path / "manifest.json").descargas
    assert sorted(saved, key=lambda r: r.archivo) == sorted(records, key=lambda r: r.archivo)


@pytest.mark.parametrize(
    "name, body",
    [
        ("rhea2ec.tsv", b"RHEA_ID\tMASTER_ID\tID\n10\t10\t7.99.99.9\n"),
        ("rhea-directions.tsv", b"MASTER\tLR\tRL\tBI\n10\t11\t12\t13\n"),
        ("rhea2ec.tsv", b""),
    ],
)
def test_changed_columns_stop_the_extraction(run_extractor, tmp_path, name, body):
    with pytest.raises(SourceFormatError, match=name):
        run_extractor(rhea.extract, FakeFtp(files(**{name: body})))


def test_missing_release_stops_before_downloading(run_extractor, tmp_path):
    server = FakeFtp(files(release=b"rhea.release.date=2026-09-02\n"))
    with pytest.raises(SourceFormatError):
        run_extractor(rhea.extract, server)
    assert server.requests == [rhea.RELEASE_URL]
    assert not (tmp_path / "raw").exists()


def test_release_change_during_download_is_detected(run_extractor, tmp_path):
    newer = b"rhea.release.number=143\nrhea.release.date=2026-10-07\n"
    server = FakeFtp(files(), {rhea.RELEASE_URL: [RELEASE, RELEASE, newer]})
    with pytest.raises(SourceFormatError, match="142 -> 143"):
        run_extractor(rhea.extract, server)


def test_only_official_rhea_urls_are_requested(run_extractor, tmp_path):
    server = FakeFtp(files())
    run_extractor(rhea.extract, server)
    assert all(url.startswith("https://ftp.expasy.org/databases/rhea/") for url in server.requests)


def test_download_date_is_recorded(run_extractor, tmp_path):
    _, (_, records) = run_extractor(rhea.extract, FakeFtp(files()))
    assert {r.fecha_descarga for r in records} == {date.today().isoformat()}


def test_parse_reactions_reads_participants_and_ec():
    reactions = {r.id: r for r in rhea.parse_reactions(REACTIONS_TEXT.splitlines())}
    master = reactions["RHEA:10"]
    assert master.direccion == "="
    assert master.definicion == "compuesto A + 2 compuesto B = polimero C + H(+)"
    assert master.izquierda == (
        rhea.Participant(chebi=("CHEBI:1",), coeficiente=1),
        rhea.Participant(chebi=("CHEBI:2",), coeficiente=2),
    )
    assert master.derecha[0] == rhea.Participant(chebi=("CHEBI:3", "CHEBI:3"), coeficiente=1)
    # La línea ENZYME continúa en la siguiente cuando es larga.
    assert master.ec == (
        "EC:7.99.99.9",
        "EC:7.99.99.8",
        "EC:7.99.99.7",
        "EC:7.99.99.6",
        "EC:7.99.99.5",
    )
    assert master.chebi == {"CHEBI:1", "CHEBI:2", "CHEBI:3", "CHEBI:4"}
    assert reactions["RHEA:11"].direccion == "=>"
    assert reactions["RHEA:11"].ec == ()
    assert reactions["RHEA:13"].direccion == "<=>"


@pytest.mark.parametrize(
    "text",
    [
        "ENTRY       RHEA:10\nDEFINITION  A = B\nEQUATION    CHEBI:1 -> CHEBI:2\n///\n",
        "ENTRY       RHEA:10\nDEFINITION  A = B\nEQUATION    CHEBI:1 = KEGG:C1\n///\n",
        "ENTRY       RHEA:10\nDEFINITION  A = B\nEQUATION    CHEBI:1 = n CHEBI:2\n///\n",
        "ENTRY       RHEA:10\nDEFINITION  A = B\n///\n",
        "ENTRY       10\nDEFINITION  A = B\nEQUATION    CHEBI:1 = CHEBI:2\n///\n",
        "ENTRY       RHEA:10\nDEFINITION  A = B\nEQUATION    CHEBI:1 = CHEBI:2\n"
        "ENZYME      9.9\n///\n",
        "ENTRY       RHEA:10\nDEFINITION  A = B\nEQUATION    CHEBI:1 = CHEBI:2\n",
    ],
)
def test_parse_reactions_rejects_unknown_formats(text):
    with pytest.raises(SourceFormatError):
        list(rhea.parse_reactions(text.splitlines()))


def test_changed_reactions_format_stops_the_extraction(run_extractor, tmp_path):
    body = gzip.compress(b"<rdf:RDF>\n</rdf:RDF>\n")
    with pytest.raises(SourceFormatError, match="rhea-reactions"):
        run_extractor(rhea.extract, FakeFtp(files(reactions=body)))


def test_downloaded_files_are_read_back(run_extractor, tmp_path):
    raw_dir, _ = run_extractor(rhea.extract, FakeFtp(files()))
    folder = raw_dir / "rhea/142"
    assert set(rhea.read_reactions(folder / "rhea-reactions.txt.gz")) == {
        "RHEA:10",
        "RHEA:11",
        "RHEA:13",
    }
    assert rhea.read_masters(folder / "rhea-directions.tsv") == {
        "RHEA:10": "RHEA:10",
        "RHEA:11": "RHEA:10",
        "RHEA:12": "RHEA:10",
        "RHEA:13": "RHEA:10",
    }
    assert rhea.read_rhea2ec(folder / "rhea2ec.tsv") == {"RHEA:10": {"EC:9.9.9.9"}}

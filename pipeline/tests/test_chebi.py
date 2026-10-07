"""Extractor de ChEBI con un servidor simulado: ninguna prueba usa la red.

Las filas de muestra solo imitan el formato de los TSV; sus IDs son ficticios y no
se usan como datos.
"""

import gzip

import pytest
from conftest import FakeFtp

from metabo.errors import SourceFormatError
from metabo.sources import chebi

README = b"""***************************************************************************
*
* Title:                 ChEBI flat files
*
* ChEBI Release:         256
*
* Date of last update:   2026-10-06
*
***************************************************************************
"""


def tsv(header: tuple[str, ...], rows: int = 1) -> bytes:
    lines = ["\t".join(header)] + ["\t".join("0" for _ in header)] * rows
    return gzip.compress(("\n".join(lines) + "\n").encode())


def files(**overrides: bytes) -> dict[str, bytes]:
    served = {chebi.README_URL: README}
    for name, header in chebi.TSV_FILES.items():
        served[f"{chebi.BASE_URL}/{name}"] = tsv(header)
    for name, body in overrides.items():
        served[f"{chebi.BASE_URL}/{name}"] = body
    return served


def test_parse_release():
    assert chebi.parse_release(README.decode()) == "256"


def test_extract_downloads_into_release_folder(run_extractor):
    raw_dir, (release, records) = run_extractor(chebi.extract, FakeFtp(files()))
    assert release == "256"
    assert [r.archivo for r in records] == ["chebi/256/README"] + [
        f"chebi/256/{name}" for name in chebi.TSV_FILES
    ]
    assert (raw_dir / "chebi/256/README").read_bytes() == README
    assert all(r.licencia == "CC BY 4.0" for r in records)


@pytest.mark.parametrize(
    "name, body",
    [
        ("compounds.tsv.gz", tsv(("id", "name"))),
        ("names.tsv.gz", gzip.compress(b"")),
        ("relation.tsv.gz", b"no es gzip"),
    ],
)
def test_changed_columns_stop_the_extraction(run_extractor, name, body):
    with pytest.raises(SourceFormatError, match=name.split(".")[0]):
        run_extractor(chebi.extract, FakeFtp(files(**{name: body})))


def test_missing_release_stops_before_downloading(run_extractor, tmp_path):
    server = FakeFtp(files(README=b"* Title: ChEBI flat files\n"))
    with pytest.raises(SourceFormatError):
        run_extractor(chebi.extract, server)
    assert server.requests == [chebi.README_URL]
    assert not (tmp_path / "raw").exists()


def test_release_change_during_download_is_detected(run_extractor):
    newer = README.replace(b"256", b"257")
    server = FakeFtp(files(), {chebi.README_URL: [README, README, newer]})
    with pytest.raises(SourceFormatError, match="256 -> 257"):
        run_extractor(chebi.extract, server)


def test_only_official_chebi_urls_are_requested(run_extractor):
    server = FakeFtp(files())
    run_extractor(chebi.extract, server)
    assert all(
        url.startswith("https://ftp.ebi.ac.uk/pub/databases/chebi/flat_files/")
        for url in server.requests
    )


def test_read_compound_names(tmp_path):
    header = chebi.TSV_FILES["compounds.tsv.gz"]
    rows = [
        dict.fromkeys(header, "0") | {"chebi_accession": "CHEBI:1", "name": "compuesto ficticio"},
        dict.fromkeys(header, "0") | {"chebi_accession": "CHEBI:2", "name": "otro\tno"},
    ]
    rows[1]["name"] = "otro compuesto"
    lines = ["\t".join(header)] + ["\t".join(r[h] for h in header) for r in rows]
    path = tmp_path / "compounds.tsv.gz"
    path.write_bytes(gzip.compress(("\n".join(lines) + "\n").encode()))
    assert chebi.read_compound_names(path) == {
        "CHEBI:1": "compuesto ficticio",
        "CHEBI:2": "otro compuesto",
    }

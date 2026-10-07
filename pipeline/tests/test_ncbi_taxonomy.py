"""Extractor y lector de NCBI Taxonomy con un servidor simulado: ninguna prueba usa la red.

El volcado de muestra solo imita el formato de new_taxdump (taxdump_readme.txt). Sus
taxones, nombres y rangos son ficticios y no se usan como datos.
"""

import hashlib
import io
import tarfile
from pathlib import Path

import httpx
import pytest
from conftest import FakeFtp

from metabo.errors import ConfigError, SourceFormatError
from metabo.sources import ncbi_taxonomy as ncbi
from metabo.sources.ncbi_taxonomy import TaxonNode

LAST_MODIFIED = "Wed, 07 Oct 2026 15:41:56 GMT"


def dmp(*rows: tuple[str, ...]) -> bytes:
    return "".join("\t|\t".join(row) + "\t|\n" for row in rows).encode("utf-8")


DUMP = {
    "delnodes.dmp": dmp(("900",)),
    "merged.dmp": dmp(("800", "13")),
    "names.dmp": dmp(
        ("10", "nodo raíz ficticio", "", "scientific name"),
        ("11", "Bacteria", "", "scientific name"),
        ("12", "Género ficticio", "", "scientific name"),
        ("13", "Género ficticio especie", "", "scientific name"),
        ("13", "bicho de prueba", "", "common name"),
        ("14", "Organismo sin dominio", "", "scientific name"),
    ),
    "nodes.dmp": dmp(
        ("10", "1", "cellular root", "x"),
        ("11", "10", "domain", "x"),
        ("12", "11", "genus", "x"),
        ("13", "12", "species", "x"),
        ("14", "10", "no rank", "x"),
    ),
    "taxidlineage.dmp": dmp(
        ("10", ""), ("11", "10"), ("12", "10 11"), ("13", "10 11 12"), ("14", "10")
    ),
}


def tar_gz(members: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for name, body in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(body)
            tar.addfile(info, io.BytesIO(body))
    return buffer.getvalue()


def md5_line(body: bytes) -> bytes:
    return f"{hashlib.md5(body).hexdigest()}  new_taxdump.tar.gz\n".encode()


class DatedFtp(FakeFtp):
    """FakeFtp que agrega Last-Modified a cada respuesta, como el FTP de NCBI."""

    def __init__(self, *args, last_modified: str | None = LAST_MODIFIED, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_modified = last_modified

    def __call__(self, request: httpx.Request) -> httpx.Response:
        response = super().__call__(request)
        if self.last_modified:
            response.headers["Last-Modified"] = self.last_modified
        return response


@pytest.fixture
def archive() -> bytes:
    return tar_gz(DUMP)


def test_extract_checks_md5_and_dates_the_dump(run_extractor, archive):
    server = DatedFtp({ncbi.MD5_URL: md5_line(archive), ncbi.ARCHIVE_URL: archive})
    raw_dir, (version, records) = run_extractor(ncbi.extract, server)
    assert version == "2026-10-07"
    assert [r.archivo for r in records] == [
        "ncbi_taxonomy/2026-10-07/new_taxdump.tar.gz.md5",
        "ncbi_taxonomy/2026-10-07/new_taxdump.tar.gz",
    ]
    assert (raw_dir / records[1].archivo).read_bytes() == archive
    assert all(r.licencia == "Dominio público" for r in records)


def test_a_dump_published_during_the_download_is_rejected(run_extractor, archive):
    newer = tar_gz(DUMP | {"merged.dmp": dmp(("801", "13"))})
    server = DatedFtp({ncbi.MD5_URL: md5_line(archive), ncbi.ARCHIVE_URL: newer})
    with pytest.raises(SourceFormatError, match="MD5"):
        run_extractor(ncbi.extract, server)


def test_a_dump_without_the_needed_files_is_rejected(run_extractor):
    incomplete = tar_gz({k: v for k, v in DUMP.items() if k != "taxidlineage.dmp"})
    server = DatedFtp({ncbi.MD5_URL: md5_line(incomplete), ncbi.ARCHIVE_URL: incomplete})
    with pytest.raises(SourceFormatError, match=r"taxidlineage\.dmp"):
        run_extractor(ncbi.extract, server)


def test_missing_last_modified_stops_the_extraction(run_extractor, archive):
    server = DatedFtp(
        {ncbi.MD5_URL: md5_line(archive), ncbi.ARCHIVE_URL: archive}, last_modified=None
    )
    with pytest.raises(SourceFormatError, match="Last-Modified"):
        run_extractor(ncbi.extract, server)


@pytest.mark.parametrize("text", ["", "abc  new_taxdump.tar.gz", "0" * 32 + "  otro.tar.gz"])
def test_unexpected_md5_format_is_rejected(text):
    with pytest.raises(SourceFormatError):
        ncbi.parse_md5(text)


@pytest.fixture
def dump_path(tmp_path: Path, archive: bytes) -> Path:
    path = tmp_path / "new_taxdump.tar.gz"
    path.write_bytes(archive)
    return path


def test_read_taxa_gives_lineage_rank_and_domain(dump_path):
    records = ncbi.read_taxa(dump_path, ["taxon:13", "taxon:14"])
    species = records["taxon:13"]
    assert species.nombre_cientifico == "Género ficticio especie"
    assert species.rango == "species"
    assert species.linaje == (
        TaxonNode("taxon:10", "nodo raíz ficticio", "cellular root"),
        TaxonNode("taxon:11", "Bacteria", "domain"),
        TaxonNode("taxon:12", "Género ficticio", "genus"),
    )
    assert species.dominio == "bacteria"
    assert records["taxon:14"].dominio is None


@pytest.mark.parametrize(
    ("taxon", "message"),
    [
        ("taxon:800", "se fusionó con taxon:13"),
        ("taxon:900", "se eliminó"),
        ("taxon:999", "no existe"),
        ("511145", "CURIE"),
    ],
)
def test_unusable_taxa_are_reported(dump_path, taxon, message):
    with pytest.raises(ConfigError, match=message):
        ncbi.read_taxa(dump_path, [taxon])


def test_unknown_domain_is_a_format_error(tmp_path):
    names = DUMP["names.dmp"].replace(b"Bacteria", b"Dominio nuevo")
    path = tmp_path / "new_taxdump.tar.gz"
    path.write_bytes(tar_gz(DUMP | {"names.dmp": names}))
    with pytest.raises(SourceFormatError, match="dominio desconocido"):
        ncbi.read_taxa(path, ["taxon:13"])

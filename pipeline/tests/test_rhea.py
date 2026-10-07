"""Extractor de Rhea con un servidor simulado: ninguna prueba usa la red.

Las filas de muestra solo imitan el formato de los TSV; sus IDs son ficticios y no
se usan como datos.
"""

from datetime import date

import httpx
import pytest

from metabo.download import Downloader
from metabo.errors import SourceFormatError
from metabo.manifest import Manifest
from metabo.registry import SourceRegistry
from metabo.sources import rhea

RELEASE = b"rhea.release.number=142\nrhea.release.date=2026-09-02\n"
DIRECTIONS = b"RHEA_ID_MASTER\tRHEA_ID_LR\tRHEA_ID_RL\tRHEA_ID_BI\n10\t11\t12\t13\n"
EC = b"RHEA_ID\tDIRECTION\tMASTER_ID\tID\n10\tUN\t10\t9.9.9.9\n"


def files(**overrides: bytes) -> dict[str, bytes]:
    served = {
        rhea.RELEASE_URL: RELEASE,
        f"{rhea.BASE_URL}/tsv/rhea-directions.tsv": DIRECTIONS,
        f"{rhea.BASE_URL}/tsv/rhea2ec.tsv": EC,
    }
    for name, body in overrides.items():
        url = rhea.RELEASE_URL if name == "release" else f"{rhea.BASE_URL}/tsv/{name}"
        served[url] = body
    return served


class FakeFtp:
    """Sirve un cuerpo por URL; `releases` permite cambiar el release entre lecturas."""

    def __init__(self, served: dict[str, bytes], releases: list[bytes] | None = None):
        self.served = served
        self.releases = list(releases or [])
        self.requests: list[str] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        self.requests.append(url)
        if url == rhea.RELEASE_URL and self.releases:
            return httpx.Response(200, content=self.releases.pop(0))
        if url not in self.served:
            return httpx.Response(404)
        return httpx.Response(200, content=self.served[url])


@pytest.fixture
def rhea_registry() -> SourceRegistry:
    # Registro real: la prueba falla si sources.yaml deja de permitir estas URLs.
    return SourceRegistry.load()


def run(rhea_registry, download_config, tmp_path, server):
    client = httpx.Client(transport=httpx.MockTransport(server), follow_redirects=True)
    raw_dir = tmp_path / "raw"
    downloader = Downloader(
        download_config, rhea_registry, raw_dir, client=client, sleep=lambda _: None
    )
    return raw_dir, rhea.extract(downloader, raw_dir)


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


def test_extract_downloads_into_release_folder(rhea_registry, download_config, tmp_path):
    raw_dir, (release, records) = run(rhea_registry, download_config, tmp_path, FakeFtp(files()))

    assert release.numero == "142"
    assert [r.archivo for r in records] == [
        "rhea/142/rhea-release.properties",
        "rhea/142/rhea-directions.tsv",
        "rhea/142/rhea2ec.tsv",
    ]
    assert (raw_dir / "rhea/142/rhea2ec.tsv").read_bytes() == EC
    assert all(r.version == "142" and r.licencia == "CC BY 4.0" for r in records)


def test_records_validate_against_manifest_schema(rhea_registry, download_config, tmp_path):
    _, (_, records) = run(rhea_registry, download_config, tmp_path, FakeFtp(files()))
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
        ("rhea2ec.tsv", b"RHEA_ID\tMASTER_ID\tID\n10\t10\t9.9.9.9\n"),
        ("rhea-directions.tsv", b"MASTER\tLR\tRL\tBI\n10\t11\t12\t13\n"),
        ("rhea2ec.tsv", b""),
    ],
)
def test_changed_columns_stop_the_extraction(rhea_registry, download_config, tmp_path, name, body):
    with pytest.raises(SourceFormatError, match=name):
        run(rhea_registry, download_config, tmp_path, FakeFtp(files(**{name: body})))


def test_missing_release_stops_before_downloading(rhea_registry, download_config, tmp_path):
    server = FakeFtp(files(release=b"rhea.release.date=2026-09-02\n"))
    with pytest.raises(SourceFormatError):
        run(rhea_registry, download_config, tmp_path, server)
    assert server.requests == [rhea.RELEASE_URL]
    assert not (tmp_path / "raw").exists()


def test_release_change_during_download_is_detected(rhea_registry, download_config, tmp_path):
    newer = b"rhea.release.number=143\nrhea.release.date=2026-10-07\n"
    server = FakeFtp(files(), releases=[RELEASE, RELEASE, newer])
    with pytest.raises(SourceFormatError, match="142 -> 143"):
        run(rhea_registry, download_config, tmp_path, server)


def test_only_official_rhea_urls_are_requested(rhea_registry, download_config, tmp_path):
    server = FakeFtp(files())
    run(rhea_registry, download_config, tmp_path, server)
    assert all(url.startswith("https://ftp.expasy.org/databases/rhea/") for url in server.requests)


def test_download_date_is_recorded(rhea_registry, download_config, tmp_path):
    _, (_, records) = run(rhea_registry, download_config, tmp_path, FakeFtp(files()))
    assert {r.fecha_descarga for r in records} == {date.today().isoformat()}

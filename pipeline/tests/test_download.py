import hashlib
from datetime import date

import httpx
import pytest

from metabo.config import DownloadConfig
from metabo.download import Downloader
from metabo.errors import ConfigError, DownloadError, SourceNotAllowedError

URL = "https://datos.ejemplo.invalid/descargas/datos.tsv"
BODY = b"id\tnombre\n1\tficticio\n"


class FakeServer:
    """Transporte HTTP simulado: responde la secuencia de estados indicada."""

    def __init__(self, *statuses: int, body: bytes = BODY, redirect_to: str | None = None):
        self.statuses = list(statuses)
        self.body = body
        self.redirect_to = redirect_to
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.redirect_to and str(request.url) != self.redirect_to:
            return httpx.Response(302, headers={"Location": self.redirect_to})
        status = self.statuses.pop(0) if len(self.statuses) > 1 else self.statuses[0]
        return httpx.Response(status, content=self.body if status == 200 else b"error")


def make_downloader(registry, config, tmp_path, server):
    sleeps: list[float] = []
    client = httpx.Client(transport=httpx.MockTransport(server), follow_redirects=True)
    downloader = Downloader(config, registry, tmp_path / "raw", client=client, sleep=sleeps.append)
    return downloader, sleeps


def test_successful_download_writes_file_and_record(registry, download_config, tmp_path):
    server = FakeServer(200)
    downloader, _ = make_downloader(registry, download_config, tmp_path, server)

    record = downloader.download("fuente_prueba", URL, "v1", today=date(2026, 10, 1))

    target = tmp_path / "raw" / "fuente_prueba" / "v1" / "datos.tsv"
    assert target.read_bytes() == BODY
    assert record.sha256 == hashlib.sha256(BODY).hexdigest()
    assert record.bytes == len(BODY)
    assert record.archivo == "fuente_prueba/v1/datos.tsv"
    assert record.fecha_descarga == "2026-10-01"
    assert record.licencia == "CC BY 4.0"
    assert not list(target.parent.glob("*.parcial"))


def test_user_agent_includes_contact(registry, download_config, tmp_path):
    server = FakeServer(200)
    downloader, _ = make_downloader(registry, download_config, tmp_path, server)
    downloader.download("fuente_prueba", URL, "v1")
    user_agent = server.requests[0].headers["User-Agent"]
    assert "mailto:pruebas@ejemplo.invalid" in user_agent
    assert user_agent.startswith("MetaboAtlas/")


@pytest.mark.parametrize("transient", [500, 503, 429])
def test_transient_errors_are_retried_with_exponential_wait(
    registry, download_config, tmp_path, transient
):
    server = FakeServer(transient, transient, 200)
    downloader, sleeps = make_downloader(registry, download_config, tmp_path, server)

    downloader.download("fuente_prueba", URL, "v1")

    assert len(server.requests) == 3
    assert len(sleeps) == 2
    assert sleeps[1] > sleeps[0] > 0


def test_retries_are_bounded(registry, download_config, tmp_path):
    server = FakeServer(503)
    downloader, _ = make_downloader(registry, download_config, tmp_path, server)

    with pytest.raises(DownloadError, match="3 intentos"):
        downloader.download("fuente_prueba", URL, "v1")

    assert len(server.requests) == download_config.reintentos
    assert not list((tmp_path / "raw").rglob("*.tsv*"))


def test_client_errors_are_not_retried(registry, download_config, tmp_path):
    server = FakeServer(404)
    downloader, _ = make_downloader(registry, download_config, tmp_path, server)

    with pytest.raises(DownloadError, match="404"):
        downloader.download("fuente_prueba", URL, "v1")

    assert len(server.requests) == 1


@pytest.mark.parametrize("key", ["fuente_pendiente", "fuente_enlace", "no_registrada"])
def test_refused_sources_make_no_request(registry, download_config, tmp_path, key):
    server = FakeServer(200)
    downloader, _ = make_downloader(registry, download_config, tmp_path, server)

    with pytest.raises(SourceNotAllowedError):
        downloader.download(key, URL, "v1")

    assert server.requests == []


def test_unofficial_url_makes_no_request(registry, download_config, tmp_path):
    server = FakeServer(200)
    downloader, _ = make_downloader(registry, download_config, tmp_path, server)

    with pytest.raises(SourceNotAllowedError, match="accesos oficiales"):
        downloader.download("fuente_prueba", "https://otro.ejemplo.invalid/x.tsv", "v1")

    assert server.requests == []


def test_redirect_outside_official_access_is_refused(registry, download_config, tmp_path):
    server = FakeServer(200, redirect_to="https://espejo.ejemplo.invalid/datos.tsv")
    downloader, _ = make_downloader(registry, download_config, tmp_path, server)

    with pytest.raises(SourceNotAllowedError):
        downloader.download("fuente_prueba", URL, "v1")

    assert not list((tmp_path / "raw").rglob("*.tsv*"))


@pytest.mark.parametrize(
    ("version", "filename"), [("..", None), ("v1", "../fuera.tsv"), ("v1/../..", None)]
)
def test_unsafe_paths_are_refused(registry, download_config, tmp_path, version, filename):
    server = FakeServer(200)
    downloader, _ = make_downloader(registry, download_config, tmp_path, server)

    with pytest.raises(DownloadError, match="no válido"):
        downloader.download("fuente_prueba", URL, version, filename=filename)

    assert server.requests == []


def test_missing_contact_blocks_downloads(registry, download_config, tmp_path):
    config = DownloadConfig(**{**download_config.model_dump(), "contacto": None})
    with pytest.raises(ConfigError, match="contacto"):
        Downloader(config, registry, tmp_path / "raw")

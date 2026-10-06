import json

import pytest

from metabo.errors import ConfigError
from metabo.manifest import DownloadRecord, Manifest


def _record(**overrides) -> DownloadRecord:
    data = {
        "fuente": "fuente_prueba",
        "url": "https://datos.ejemplo.invalid/descargas/a.tsv",
        "version": "v1",
        "fecha_descarga": "2026-10-01",
        "archivo": "fuente_prueba/v1/a.tsv",
        "sha256": "0" * 64,
        "bytes": 10,
        "licencia": "CC BY 4.0",
    }
    data.update(overrides)
    return DownloadRecord(**data)


def test_written_manifest_validates_and_round_trips(tmp_path):
    manifest = Manifest(version_datos="2026.10")
    manifest.add(_record())
    path = tmp_path / "manifest.json"
    manifest.write(path)

    data = json.loads(path.read_text())
    assert data["generado"].endswith("Z")
    assert Manifest.read(path).descargas == manifest.descargas


def test_same_file_replaces_previous_record():
    manifest = Manifest(version_datos="2026.10")
    manifest.add(_record(sha256="0" * 64))
    manifest.add(_record(sha256="1" * 64))
    assert [d.sha256 for d in manifest.descargas] == ["1" * 64]


def test_invalid_checksum_is_rejected_on_write(tmp_path):
    manifest = Manifest(version_datos="2026.10")
    manifest.add(_record(sha256="no-es-sha"))
    with pytest.raises(ConfigError, match="manifiesto"):
        manifest.write(tmp_path / "manifest.json")
    assert not (tmp_path / "manifest.json").exists()


def test_invalid_data_version_is_rejected_on_write(tmp_path):
    with pytest.raises(ConfigError):
        Manifest(version_datos="octubre").write(tmp_path / "manifest.json")

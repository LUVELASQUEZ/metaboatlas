import pytest
import yaml
from conftest import FAKE_SOURCES

from metabo.errors import ConfigError, SourceNotAllowedError
from metabo.registry import SourceRegistry


def test_repository_sources_load():
    registry = SourceRegistry.load()
    assert registry.get("rhea").nombre == "Rhea"


def test_no_repository_source_is_downloadable_until_verified():
    # Fase 0: todas las fuentes están "pendiente de verificar".
    for source in SourceRegistry.load():
        if source.estado != "verificada":
            assert not source.downloadable


def test_link_only_sources_are_never_downloadable():
    for source in SourceRegistry.load():
        if source.uso == "solo_enlace":
            with pytest.raises(SourceNotAllowedError, match="solo enlace"):
                SourceRegistry.load().require_downloadable(source.key)


def test_verified_source_is_downloadable(registry):
    assert registry.require_downloadable("fuente_prueba").downloadable


@pytest.mark.parametrize(
    ("key", "message"),
    [
        ("fuente_pendiente", "pendiente de verificar"),
        ("fuente_enlace", "solo enlace"),
        ("no_registrada", "no está registrada"),
    ],
)
def test_non_downloadable_sources_are_refused(registry, key, message):
    with pytest.raises(SourceNotAllowedError, match=message):
        registry.require_downloadable(key)


@pytest.mark.parametrize(
    "url",
    [
        "https://datos.ejemplo.invalid/descargas/archivo.tsv",
        "https://datos.ejemplo.invalid/descargas/sub/archivo.tsv.gz",
    ],
)
def test_official_urls_are_accepted(registry, url):
    registry.require_official_url(registry.get("fuente_prueba"), url)


@pytest.mark.parametrize(
    "url",
    [
        "http://datos.ejemplo.invalid/descargas/archivo.tsv",
        "https://datos.ejemplo.invalid/otra-ruta/archivo.tsv",
        "https://datos.ejemplo.invalid.atacante.example/descargas/archivo.tsv",
        "https://otro.ejemplo.invalid/descargas/archivo.tsv",
    ],
    ids=["sin-https", "otra-ruta", "dominio-impostor", "otro-dominio"],
)
def test_unofficial_urls_are_refused(registry, url):
    with pytest.raises(SourceNotAllowedError):
        registry.require_official_url(registry.get("fuente_prueba"), url)


def test_prefix_without_trailing_slash_respects_boundaries(tmp_path):
    data = {"fuente_prueba": dict(FAKE_SOURCES["fuente_prueba"], acceso=["api.ejemplo.invalid"])}
    path = tmp_path / "sources.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    registry = SourceRegistry.load(path)
    source = registry.get("fuente_prueba")
    registry.require_official_url(source, "https://api.ejemplo.invalid/consulta")
    with pytest.raises(SourceNotAllowedError):
        registry.require_official_url(source, "https://api.ejemplo.invalidx/consulta")


def test_build_link_from_template(registry):
    url = registry.build_link("fuente_enlace", "entrada", "C00000")
    assert url == "https://enlace.ejemplo.invalid/entry/C00000"


def test_build_link_escapes_ids(registry):
    url = registry.build_link("fuente_prueba", "registro", "a b/../c")
    assert url == "https://datos.ejemplo.invalid/registro/a%20b%2F..%2Fc"


def test_repository_kegg_link_uses_template():
    url = SourceRegistry.load().build_link("kegg", "via_referencia", "map00010")
    assert url == "https://www.kegg.jp/pathway/map00010"


def test_unknown_template_is_an_error(registry):
    with pytest.raises(ConfigError, match="no tiene la plantilla"):
        registry.build_link("fuente_prueba", "inexistente", "1")


def test_invalid_sources_file_is_rejected(tmp_path):
    path = tmp_path / "sources.yaml"
    path.write_text(yaml.safe_dump({"mala": {"nombre": "Sin campos"}}), encoding="utf-8")
    with pytest.raises(ConfigError, match=r"fuentes\.schema\.json"):
        SourceRegistry.load(path)

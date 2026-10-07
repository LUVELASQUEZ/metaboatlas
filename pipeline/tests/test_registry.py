import pytest
import yaml
from conftest import FAKE_SOURCES

from metabo.errors import ConfigError, SourceNotAllowedError
from metabo.registry import SourceRegistry


def test_repository_sources_load():
    registry = SourceRegistry.load()
    assert registry.get("rhea").nombre == "Rhea"


def test_no_repository_source_is_downloadable_until_verified():
    for source in SourceRegistry.load():
        if source.estado != "verificada":
            assert not source.downloadable


PHASE_0_SOURCES = ["rhea", "chebi", "uniprot", "enzyme", "ncbi_taxonomy"]


@pytest.mark.parametrize("key", PHASE_0_SOURCES)
def test_phase_0_sources_are_verified_and_downloadable(key):
    source = SourceRegistry.load().require_downloadable(key)
    assert source.acceso


def test_verified_repository_sources_are_complete():
    # Una fuente verificada que se redistribuye debe poder citarse y rastrearse:
    # el esquema exige licencia, URL de licencia, fecha y cita; aquí además el DOI,
    # la página principal y las plantillas de enlace.
    for source in SourceRegistry.load():
        if source.estado == "verificada" and source.uso == "redistribuir":
            assert source.url and source.url.startswith("https://"), source.key
            assert source.licencia_url, source.key
            assert source.verificada, source.key
            assert source.cita_recomendada, source.key
            assert source.doi_cita, source.key
            assert "TODO" not in source.cita_recomendada, source.key
            assert source.plantillas, source.key


@pytest.mark.parametrize(
    ("fuente", "tipo", "id", "expected"),
    [
        ("rhea", "reaccion", "16109", "https://www.rhea-db.org/rhea/16109"),
        ("chebi", "compuesto", "15361", "https://www.ebi.ac.uk/chebi/CHEBI:15361"),
        ("uniprot", "proteina", "P0A6T1", "https://www.uniprot.org/uniprotkb/P0A6T1"),
        ("enzyme", "enzima", "2.7.1.1", "https://enzyme.expasy.org/EC/2.7.1.1"),
        (
            "ncbi_taxonomy",
            "organismo",
            "511145",
            "https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=511145",
        ),
    ],
)
def test_repository_phase_0_links(fuente, tipo, id, expected):
    assert SourceRegistry.load().build_link(fuente, tipo, id) == expected


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

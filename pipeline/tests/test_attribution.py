"""ATRIBUCION.md del paquete, con el sources.yaml real y un manifiesto de prueba."""

from metabo.export.attribution import attribution
from metabo.manifest import DownloadRecord, Manifest
from metabo.registry import SourceRegistry


def _record(fuente: str, version: str, archivo: str) -> DownloadRecord:
    return DownloadRecord(
        fuente=fuente,
        url=f"https://datos.ejemplo.invalid/{archivo}",
        version=version,
        fecha_descarga="2026-10-07",
        archivo=f"{fuente}/{version}/{archivo}",
        sha256="0" * 64,
        bytes=1,
        licencia="CC BY 4.0",
    )


def test_attribution_lists_each_source_with_its_license_and_citation():
    manifest = Manifest(
        version_datos="2026.10",
        descargas=[
            _record("rhea", "142", "rhea2ec.tsv"),
            _record("rhea", "142", "rhea-directions.tsv"),
            _record("ncbi_taxonomy", "2026-10-07", "new_taxdump.tar.gz"),
        ],
    )
    registry = SourceRegistry.load()
    text = attribution(manifest, registry)
    assert text.startswith("# Paquete de datos de MetaboAtlas 2026.10")
    assert "## NCBI Taxonomy" in text and "## Rhea" in text
    assert "## ChEBI" not in text  # solo las fuentes del paquete
    assert text.count("Versión 142,") == 1  # una línea por versión, no por archivo
    rhea = registry.get("rhea")
    assert f"https://doi.org/{rhea.doi_cita}" in text
    # La cita se copia tal cual de sources.yaml, línea por línea.
    for line in rhea.cita_recomendada.splitlines():
        assert f"> {line}" in text
    assert "no significa que el organismo carezca" in text


def test_source_without_official_citation_says_so():
    manifest = Manifest(
        version_datos="2026.10",
        descargas=[_record("wikidata", "2026-10-08", "compuestos-001.json")],
    )
    registry = SourceRegistry.load()
    assert registry.get("wikidata").sin_cita_oficial
    text = attribution(manifest, registry)
    assert "## Wikidata" in text
    assert "Cita recomendada" not in text
    assert "no publica una cita recomendada" in text

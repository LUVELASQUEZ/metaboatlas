"""Extractor de UniProt con un servidor simulado: ninguna prueba usa la red.

Los proteomas, accesiones y proteínas de muestra son ficticios (UP000000001,
X00001, …); solo imitan el formato de la API y no se usan como datos.
"""

import gzip
import json

import httpx
import pytest

from metabo.errors import ConfigError, SourceFormatError
from metabo.organisms import Organism
from metabo.sources import uniprot

RELEASE = "2026_03"
UP1, UP2 = "UP000000001", "UP000000002"
ORGANISMS = [
    Organism(id="taxon:1", nombre="Organismo uno", intereses=["modelo"], proteoma_referencia=UP1),
    Organism(id="taxon:2", nombre="Organismo dos", intereses=["modelo"], proteoma_referencia=UP2),
]
HEADER = "\t".join(uniprot.FIELDS.values())


def proteome(up: str, count: int = 2, kind: str = "Reference proteome") -> bytes:
    return json.dumps({"id": up, "proteomeType": kind, "proteinCount": count}).encode()


def proteins(rows: int = 2, header: str = HEADER) -> bytes:
    lines = [header] + [
        "\t".join([f"X0000{i}"] + [""] * (len(uniprot.FIELDS) - 1)) for i in range(rows)
    ]
    return gzip.compress(("\n".join(lines) + "\n").encode())


class FakeUniprot:
    """Responde por URL con su cuerpo y la cabecera X-UniProt-Release."""

    def __init__(self, bodies: dict[str, bytes], releases: dict[str, str] | None = None):
        self.bodies = bodies
        self.releases = releases or {}
        self.requests: list[str] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        self.requests.append(url)
        if url not in self.bodies:
            return httpx.Response(404)
        headers = {}
        if self.releases.get(url, RELEASE):
            headers[uniprot.RELEASE_HEADER] = self.releases.get(url, RELEASE)
        return httpx.Response(200, content=self.bodies[url], headers=headers)


def bodies(**overrides: bytes) -> dict[str, bytes]:
    served = {}
    for up in (UP1, UP2):
        served[uniprot.proteome_url(up)] = overrides.get(f"{up}.json", proteome(up))
        served[uniprot.proteins_url(up)] = overrides.get(f"{up}.tsv.gz", proteins())
    return served


def run(run_extractor, server, organisms=ORGANISMS):
    return run_extractor(lambda d, r: uniprot.extract(d, r, organisms=organisms), server)


def test_field_headers_match_requested_fields():
    url = uniprot.proteins_url(UP1)
    assert "query=proteome%3AUP000000001" in url
    assert "fields=" + "%2C".join(uniprot.FIELDS) in url
    assert url.startswith("https://rest.uniprot.org/uniprotkb/stream?")


def test_extract_downloads_each_proteome_into_release_folder(run_extractor):
    raw_dir, (version, records) = run(run_extractor, FakeUniprot(bodies()))
    assert version == RELEASE
    assert [r.archivo for r in records] == [
        f"uniprot/{RELEASE}/{UP1}.json",
        f"uniprot/{RELEASE}/{UP1}.tsv.gz",
        f"uniprot/{RELEASE}/{UP2}.json",
        f"uniprot/{RELEASE}/{UP2}.tsv.gz",
    ]
    assert (raw_dir / f"uniprot/{RELEASE}/{UP2}.tsv.gz").read_bytes() == proteins()
    assert all(r.licencia == "CC BY 4.0" and r.version == RELEASE for r in records)


def test_release_change_during_extraction_stops_it(run_extractor):
    server = FakeUniprot(bodies(), releases={uniprot.proteins_url(UP2): "2026_04"})
    with pytest.raises(SourceFormatError, match="2026_04"):
        run(run_extractor, server)


def test_missing_release_header_stops_the_extraction(run_extractor):
    server = FakeUniprot(bodies(), releases={uniprot.proteome_url(UP1): ""})
    with pytest.raises(SourceFormatError, match=uniprot.RELEASE_HEADER):
        run(run_extractor, server)


@pytest.mark.parametrize(
    "name, body, message",
    [
        (f"{UP1}.tsv.gz", proteins(header=HEADER.replace("Rhea ID", "Rhea")), "columnas"),
        (f"{UP1}.tsv.gz", proteins(rows=1), "incompleta"),
        (f"{UP2}.json", proteome(UP2, kind="Other proteome"), "referencia"),
        (f"{UP2}.json", proteome(UP1), "no es la ficha"),
        (f"{UP2}.json", b"<html>", "No se pudo leer"),
    ],
)
def test_changed_or_incomplete_data_stops_the_extraction(run_extractor, name, body, message):
    with pytest.raises(SourceFormatError, match=message):
        run(run_extractor, FakeUniprot(bodies(**{name: body})))


def test_organism_without_proteome_is_reported(run_extractor):
    organisms = [*ORGANISMS, Organism(id="taxon:3", nombre="Sin proteoma", intereses=["modelo"])]
    with pytest.raises(ConfigError, match="taxon:3"):
        run(run_extractor, FakeUniprot(bodies()), organisms)


def test_only_official_uniprot_urls_are_requested(run_extractor):
    server = FakeUniprot(bodies())
    run(run_extractor, server)
    assert server.requests
    assert all(
        url.startswith(
            ("https://rest.uniprot.org/proteomes/", "https://rest.uniprot.org/uniprotkb/stream?")
        )
        for url in server.requests
    )


def test_default_organism_list_has_a_proteome_for_every_organism():
    from metabo.organisms import load_organisms

    assert all(o.proteoma_referencia for o in load_organisms())

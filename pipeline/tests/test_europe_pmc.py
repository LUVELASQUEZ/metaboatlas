"""Extractor de Europe PMC con un servidor simulado: ninguna prueba usa la red.

Las respuestas imitan el formato JSON "lite" de la API REST; sus PMID, títulos y
autores son ficticios y no se usan como datos.
"""

import json
from datetime import date
from pathlib import Path

import httpx
import pytest
from conftest import FakeFtp

from metabo.errors import SourceFormatError
from metabo.sources import europe_pmc


def lite(*pmids: str, **extra) -> bytes:
    rows = [
        {
            "pmid": p,
            "pmcid": f"PMC{p}",
            "doi": f"10.0000/{p}",
            "title": f"Artículo <i>ficticio</i> {p}.",
            "authorString": "Autora A, Autor B.",
            "journalTitle": "Rev Ficticia",
            "journalVolume": "1",
            "issue": "2",
            "pageInfo": "3-4",
            "pubYear": "2020",
            "isOpenAccess": "Y",
            **extra,
        }
        for p in pmids
    ]
    return json.dumps({"version": "6.9", "resultList": {"result": rows}}).encode()


def served_url(pmids):
    return str(httpx.URL(europe_pmc.query_url(pmids)))


def extract_pmids(pmids):
    def run(downloader, raw_dir):
        return europe_pmc.extract(downloader, raw_dir, pmids, date(2026, 10, 8))

    return run


def test_query_asks_for_medline_ids_without_abstracts():
    url = europe_pmc.query_url(["2", "1"])
    assert "resultType=lite" in url
    assert europe_pmc.query(["2", "1"]) == "(EXT_ID:2 OR EXT_ID:1) AND SRC:MED"


@pytest.mark.parametrize("pmid", ["", "PMID:1", "1 OR 2", "01"])
def test_query_rejects_anything_but_a_pmid(pmid):
    with pytest.raises(ValueError):
        europe_pmc.query([pmid])


def test_pmids_are_sorted_in_batches():
    pmids = [str(n) for n in range(1, europe_pmc.LOTE + 2)]
    batches = europe_pmc.batches(pmids)
    assert [name for name, _ in batches] == ["referencias-001.json", "referencias-002.json"]
    assert batches[0][1][:3] == ["1", "2", "3"]


def test_extract_saves_the_response_with_the_query_date(run_extractor):
    server = FakeFtp({served_url(["1", "2"]): lite("1", "2")})
    _, (version, records) = run_extractor(extract_pmids(["2", "1"]), server)
    assert version == "2026-10-08"
    assert [r.archivo for r in records] == ["europe_pmc/2026-10-08/referencias-001.json"]


def test_a_missing_pmid_stops_the_extraction(run_extractor):
    server = FakeFtp({served_url(["1", "2"]): lite("1")})
    with pytest.raises(SourceFormatError, match="no tiene los PMID 2"):
        run_extractor(extract_pmids(["1", "2"]), server)


def test_abstracts_are_never_stored(run_extractor):
    server = FakeFtp({served_url(["1"]): lite("1", abstractText="Resumen.")})
    with pytest.raises(SourceFormatError, match="resúmenes"):
        run_extractor(extract_pmids(["1"]), server)


def test_articles_keep_citation_data_without_html(tmp_path: Path):
    path = tmp_path / "referencias-001.json"
    path.write_bytes(lite("7"))
    article = europe_pmc.read_articles([path])["7"]
    assert article.titulo == "Artículo ficticio 7."
    assert (article.anio, article.pmcid, article.acceso_abierto) == (2020, "PMC7", True)

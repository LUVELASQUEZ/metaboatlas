"""Extractor de Wikidata con un servidor simulado: ninguna prueba usa la red.

Las respuestas imitan el formato SPARQL JSON de query.wikidata.org; sus IDs y
etiquetas son ficticios y no se usan como datos.
"""

import json
from datetime import date
from pathlib import Path

import httpx
import pytest
from conftest import FakeFtp

from metabo.errors import SourceFormatError
from metabo.sources import wikidata


def sparql(*rows):
    bindings = []
    for native, qid, es in rows:
        row = {
            "id": {"type": "literal", "value": native},
            "item": {"type": "uri", "value": f"http://www.wikidata.org/entity/{qid}"},
        }
        if es is not None:
            row["es"] = {"xml:lang": "es", "type": "literal", "value": es}
        bindings.append(row)
    return json.dumps({"head": {"vars": ["id", "item", "es"]}, "results": {"bindings": bindings}})


def served_url(tipo, ids):
    # httpx normaliza la URL igual que al pedirla; así coincide con la del servidor.
    return str(httpx.URL(wikidata.query_url(tipo, ids)))


def extract_with():
    def run(downloader, raw_dir):
        return wikidata.extract(
            downloader, raw_dir, ["CHEBI:2", "CHEBI:1"], ["EC:7.99.99.1"], date(2026, 10, 8)
        )

    return run


def test_query_uses_the_property_of_each_type():
    query = wikidata.query("compuestos", ["CHEBI:15361", "CHEBI:4167"])
    assert 'VALUES ?id { "15361" "4167" }' in query
    assert "wdt:P683" in query
    assert "wdt:P591" in wikidata.query("enzimas", ["EC:2.7.1.1"])


@pytest.mark.parametrize("curie", ["EC:2.7.1.1", "CHEBI:", 'CHEBI:1" } ?x ?y {'])
def test_query_rejects_ids_of_another_type_or_with_quotes(curie):
    with pytest.raises(ValueError):
        wikidata.query("compuestos", [curie])


def test_ids_are_split_in_batches():
    ids = [f"CHEBI:{n}" for n in range(wikidata.LOTE + 1)]
    batches = wikidata.file_names("compuestos", ids)
    assert [name for name, _ in batches] == ["compuestos-001.json", "compuestos-002.json"]
    assert sum(len(lote) for _, lote in batches) == wikidata.LOTE + 1


def test_extract_saves_each_response_with_the_query_date(run_extractor):
    compounds = sparql(("1", "Q1", "uno"))
    enzymes = sparql()
    server = FakeFtp(
        {
            served_url("compuestos", ["CHEBI:1", "CHEBI:2"]): compounds.encode(),
            served_url("enzimas", ["EC:7.99.99.1"]): enzymes.encode(),
        }
    )
    raw_dir, (version, records) = run_extractor(extract_with(), server)
    assert json.loads((raw_dir / records[0].archivo).read_text())["results"]["bindings"]
    assert version == "2026-10-08"
    assert [r.archivo for r in records] == [
        "wikidata/2026-10-08/compuestos-001.json",
        "wikidata/2026-10-08/enzimas-001.json",
    ]
    assert all(r.licencia == "CC0 1.0" for r in records)
    assert all(r.url.startswith("https://query.wikidata.org/sparql?") for r in records)


def test_extract_stops_on_an_unexpected_format(run_extractor):
    server = FakeFtp(
        {
            served_url("compuestos", ["CHEBI:1", "CHEBI:2"]): b'{"head": {"vars": ["x"]}}',
            served_url("enzimas", ["EC:7.99.99.1"]): sparql().encode(),
        }
    )
    with pytest.raises(SourceFormatError, match=r"head\.vars"):
        run_extractor(extract_with(), server)


def test_labels_are_used_only_when_unambiguous(tmp_path: Path):
    path = tmp_path / "enzimas-001.json"
    path.write_text(
        sparql(
            ("1.1.1.1", "Q5", "única"),
            ("1.1.1.1", "Q4", "única"),  # misma etiqueta en dos elementos: se usa
            ("2.2.2.2", "Q6", "una"),
            ("2.2.2.2", "Q7", "otra"),  # dos etiquetas distintas: ambigua
            ("3.3.3.3", "Q8", None),  # sin etiqueta en español
        ),
        encoding="utf-8",
    )
    labels = wikidata.read_labels([path], "enzimas")
    assert labels == {"EC:1.1.1.1": wikidata.Label(qid="Q4", es="única")}

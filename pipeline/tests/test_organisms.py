import pytest
import yaml

from metabo.errors import ConfigError
from metabo.organisms import load_organisms


def test_repository_organisms_are_valid_and_unique():
    organisms = load_organisms()
    assert organisms, "La lista de organismos no puede estar vacía."
    ids = [o.id for o in organisms]
    assert len(ids) == len(set(ids))


def test_phase_0_organisms_are_present():
    ids = {o.id for o in load_organisms()}
    assert {"taxon:511145", "taxon:224308", "taxon:559292", "taxon:9606"} <= ids


def test_every_repository_organism_has_a_reference_proteome():
    # El extractor de UniProt descarga las proteínas por proteoma.
    for organism in load_organisms():
        assert organism.proteoma_referencia, organism.id


def test_reference_proteomes_are_unique():
    proteomes = [o.proteoma_referencia for o in load_organisms()]
    assert len(proteomes) == len(set(proteomes))


def test_every_repository_organism_has_its_ncbi_name():
    # nombre_ncbi se copia de names.dmp de NCBI Taxonomy (ver organismos.yaml).
    for organism in load_organisms():
        assert organism.nombre_ncbi, organism.id


def test_ncbi_name_matches_the_curated_name():
    # Detecta un taxón equivocado: género y especie deben coincidir con NCBI.
    for organism in load_organisms():
        assert organism.nombre.split()[:2] == organism.nombre_ncbi.split()[:2], organism.id


def test_phase_0_ncbi_names():
    names = {o.id: o.nombre_ncbi for o in load_organisms()}
    assert names["taxon:511145"] == "Escherichia coli str. K-12 substr. MG1655"
    assert names["taxon:224308"] == "Bacillus subtilis subsp. subtilis str. 168"
    assert names["taxon:559292"] == "Saccharomyces cerevisiae S288C"
    assert names["taxon:9606"] == "Homo sapiens"


def _write(tmp_path, organismos):
    path = tmp_path / "organismos.yaml"
    path.write_text(yaml.safe_dump({"organismos": organismos}), encoding="utf-8")
    return path


@pytest.mark.parametrize("count", [1, 2, 7])
def test_any_number_of_organisms_is_accepted(tmp_path, count):
    organismos = [
        {"id": f"taxon:{n + 1}", "nombre": f"Organismo {n}", "intereses": ["modelo"]}
        for n in range(count)
    ]
    assert len(load_organisms(_write(tmp_path, organismos))) == count


def test_taxon_id_without_prefix(tmp_path):
    path = _write(tmp_path, [{"id": "taxon:511145", "nombre": "X", "intereses": ["modelo"]}])
    assert load_organisms(path)[0].taxon_id == "511145"


@pytest.mark.parametrize(
    "organismos",
    [
        [],
        [{"id": "511145", "nombre": "Sin prefijo", "intereses": ["modelo"]}],
        [{"id": "taxon:1", "nombre": "Sin intereses", "intereses": []}],
        [{"id": "taxon:1", "nombre": "X", "intereses": ["modelo"], "proteoma_referencia": "123"}],
        [{"id": "taxon:1", "nombre": "X", "intereses": ["modelo"], "nombre_ncbi": ""}],
        [
            {"id": "taxon:1", "nombre": "A", "intereses": ["modelo"]},
            {"id": "taxon:1", "nombre": "B", "intereses": ["clinico"]},
        ],
    ],
    ids=[
        "vacia",
        "sin-prefijo",
        "sin-intereses",
        "proteoma-invalido",
        "nombre-ncbi-vacio",
        "repetido",
    ],
)
def test_invalid_organism_lists_are_rejected(tmp_path, organismos):
    with pytest.raises(ConfigError):
        load_organisms(_write(tmp_path, organismos))

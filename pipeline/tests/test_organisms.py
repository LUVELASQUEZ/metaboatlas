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
        [
            {"id": "taxon:1", "nombre": "A", "intereses": ["modelo"]},
            {"id": "taxon:1", "nombre": "B", "intereses": ["clinico"]},
        ],
    ],
    ids=["vacia", "sin-prefijo", "sin-intereses", "proteoma-invalido", "repetido"],
)
def test_invalid_organism_lists_are_rejected(tmp_path, organismos):
    with pytest.raises(ConfigError):
        load_organisms(_write(tmp_path, organismos))

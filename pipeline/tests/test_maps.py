"""Verificación de los mapas curados con una vía y reacciones ficticias.

IDs, nombres y reacciones son ficticios: prueban la lógica, no son datos.
"""

import copy

from metabo.maps import check_map
from metabo.sources.rhea import Participant, Reaction


def _reaction(rid: str, left: list[str], right: list[str]) -> Reaction:
    return Reaction(
        id=rid,
        definicion="reacción ficticia",
        direccion="UN",
        izquierda=tuple(Participant((c,), 1) for c in left),
        derecha=tuple(Participant((c,), 1) for c in right),
        ec=(),
    )


# 1 + moneda(3) = 2 + protón(4); 2 = 5. El nodo 20 es un ancestro de 2 en ChEBI.
REACTIONS = {
    "RHEA:1000": _reaction("RHEA:1000", ["CHEBI:1", "CHEBI:3"], ["CHEBI:2", "CHEBI:4"]),
    "RHEA:2000": _reaction("RHEA:2000", ["CHEBI:5"], ["CHEBI:2"]),
}
ONTOLOGY = {"CHEBI:2": frozenset({"CHEBI:20"})}
COFACTORS = {"CHEBI:3", "CHEBI:4"}

VIA = {
    "id": "via:prueba",
    "modulos": [{"id": "m1", "pasos": ["p01", "p02"]}],
    "pasos": [
        {"id": "p01", "reacciones": ["RHEA:1000"], "espontaneo": False},
        {"id": "p02", "reacciones": ["RHEA:2000"], "espontaneo": False},
    ],
}

MAPA = {
    "via": "via:prueba",
    "lienzo": {"ancho": 400, "alto": 500},
    "compuestos": [
        {"compuesto": "CHEBI:1", "x": 200, "y": 50},
        {"compuesto": "CHEBI:20", "x": 200, "y": 250},
        {"compuesto": "CHEBI:5", "x": 200, "y": 450, "etiqueta": "derecha"},
    ],
    "pasos": [
        {
            "paso": "p01",
            "desde": ["CHEBI:1"],
            "hacia": ["CHEBI:20"],
            "rotulo": {"x": 200, "y": 150},
            "cofactores": "derecha",
        },
        {
            # En el sentido de la vía, al revés de la reacción de Rhea.
            "paso": "p02",
            "desde": ["CHEBI:20"],
            "hacia": ["CHEBI:5"],
            "rotulo": {"x": 200, "y": 350},
            "cofactores": "izquierda",
        },
    ],
    "modulos": [{"modulo": "m1", "x": 10, "y": 10, "ancho": 380, "alto": 480}],
    "portales": [],
}


def errors(mapa=MAPA, via=VIA) -> list[str]:
    return check_map(mapa, via, REACTIONS, ONTOLOGY, COFACTORS)


def edited(change) -> dict:
    mapa = copy.deepcopy(MAPA)
    change(mapa)
    return mapa


def test_coherent_map_has_no_errors():
    # Incluye un nodo más general que el participante (20 es ancestro de 2) y una
    # flecha en sentido contrario al de la reacción de Rhea.
    assert errors() == []


def test_schema_errors_are_reported_first():
    found = errors(edited(lambda m: m.pop("pasos")))
    assert found and all(e.startswith("esquema:") for e in found)


def test_map_of_another_pathway():
    assert errors(edited(lambda m: m.update(via="via:otra"))) == [
        "el mapa es de via:otra y la vía es via:prueba."
    ]


def test_items_outside_the_canvas():
    def change(m):
        m["compuestos"][0]["x"] = 401
        m["pasos"][1]["rotulo"]["y"] = -1
        m["modulos"][0]["alto"] = 491

    assert errors(edited(change)) == [
        "compuesto CHEBI:1 está fuera del lienzo (401, 50).",
        "rótulo de p02 está fuera del lienzo (200, -1).",
        "la región de m1 se sale del lienzo.",
    ]


def test_cofactor_cannot_be_a_node():
    found = errors(
        edited(lambda m: m["compuestos"].append({"compuesto": "CHEBI:3", "x": 1, "y": 1}))
    )
    assert found == ["CHEBI:3 es un cofactor: se dibuja junto a las flechas, no como nodo."]


def test_duplicate_node():
    found = errors(
        edited(lambda m: m["compuestos"].append({"compuesto": "CHEBI:5", "x": 1, "y": 1}))
    )
    assert found == ["CHEBI:5 está 2 veces en `compuestos`."]


def test_every_step_and_module_is_drawn_once():
    def change(m):
        m["pasos"].pop()
        m["pasos"].append({**MAPA["pasos"][0], "paso": "p09"})
        m["modulos"].append({**MAPA["modulos"][0]})

    assert errors(edited(change)) == [
        "el paso p02 debe dibujarse una vez (está 0).",
        "el paso p09 no existe en la vía.",
        "el módulo m1 debe dibujarse una vez (está 2).",
    ]


def test_arrow_compounds_must_be_nodes():
    found = errors(edited(lambda m: m["compuestos"].pop(0)))
    assert "p01: CHEBI:1 no está en `compuestos`." in found


def test_arrow_must_cross_the_reaction():
    # 1 y 3 están del mismo lado de RHEA:1000.
    found = errors(edited(lambda m: m["pasos"][0].update(hacia=["CHEBI:5"])))
    assert found == [
        "p01: la flecha ['CHEBI:1'] -> ['CHEBI:5'] no corresponde a lados opuestos de "
        "ninguna reacción Rhea del paso."
    ]


def test_a_more_specific_node_does_not_match():
    # El nodo puede ser más general que el participante, no al revés.
    reactions = {**REACTIONS, "RHEA:1000": _reaction("RHEA:1000", ["CHEBI:1"], ["CHEBI:20"])}
    mapa = edited(lambda m: m["compuestos"][1].update(compuesto="CHEBI:2"))
    for step in mapa["pasos"]:
        step["desde"] = ["CHEBI:2" if c == "CHEBI:20" else c for c in step["desde"]]
        step["hacia"] = ["CHEBI:2" if c == "CHEBI:20" else c for c in step["hacia"]]
    found = check_map(mapa, VIA, reactions, ONTOLOGY, COFACTORS)
    assert len(found) == 1 and found[0].startswith("p01: la flecha")


def test_unknown_reaction():
    via = copy.deepcopy(VIA)
    via["pasos"][1]["reacciones"] = ["RHEA:9000"]
    assert errors(via=via) == [
        "p02: RHEA:9000 no existe en Rhea.",
        "p02: la flecha ['CHEBI:20'] -> ['CHEBI:5'] no corresponde a lados opuestos de "
        "ninguna reacción Rhea del paso.",
    ]


def test_spontaneous_step_without_reactions_is_not_checked_against_rhea():
    via = copy.deepcopy(VIA)
    via["pasos"][1].update(reacciones=[], espontaneo=True)
    assert errors(via=via) == []

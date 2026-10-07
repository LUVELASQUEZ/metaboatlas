"""Verificación de los mapas curados (curation/mapas/<slug>.json) contra su vía.

El mapa guarda solo posiciones (sección 7 de docs/MANUAL.md). Para que el dibujo no
contradiga los datos, cada flecha debe corresponder a una reacción Rhea de su paso:
sus compuestos de origen en un lado de la reacción y los de destino en el otro.

Un nodo puede mostrar un compuesto más general que el participante de Rhea cuando
ChEBI dice que el participante "es un" ese compuesto, o que es su ácido o base
conjugado. Así la glucosa 6-fosfato se dibuja una sola vez aunque la hexocinasa
produzca D-glucopyranose 6-phosphate y la isomerasa consuma su anómero alfa.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping, Set
from pathlib import Path
from typing import Any

from metabo.errors import ConfigError
from metabo.schemas import validation_errors
from metabo.sources.chebi import ancestors
from metabo.sources.rhea import Reaction


def load_map(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"No se pudo leer {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"{path} debe contener un objeto con el mapa.")
    return data


def _matches(node: str, participant: str, ontology: Mapping[str, frozenset[str]]) -> bool:
    return node == participant or node in ancestors(participant, ontology)


def _side_matches(
    nodes: list[str], side: frozenset[str], ontology: Mapping[str, frozenset[str]]
) -> bool:
    return all(any(_matches(n, p, ontology) for p in side) for n in nodes)


def check_map(
    mapa: Mapping[str, Any],
    via: Mapping[str, Any],
    reactions: Mapping[str, Reaction],
    ontology: Mapping[str, frozenset[str]],
    cofactors: Set[str],
) -> list[str]:
    """Todos los errores del mapa de una vía; lista vacía si es coherente."""
    errors = [f"esquema: {e}" for e in validation_errors("mapa", mapa)]
    if errors:
        return errors
    if mapa["via"] != via["id"]:
        errors.append(f"el mapa es de {mapa['via']} y la vía es {via['id']}.")

    ancho, alto = mapa["lienzo"]["ancho"], mapa["lienzo"]["alto"]
    positioned = [(f"compuesto {n['compuesto']}", n["x"], n["y"]) for n in mapa["compuestos"]] + [
        (f"rótulo de {s['paso']}", s["rotulo"]["x"], s["rotulo"]["y"]) for s in mapa["pasos"]
    ]
    for label, x, y in positioned:
        if not (0 <= x <= ancho and 0 <= y <= alto):
            errors.append(f"{label} está fuera del lienzo ({x}, {y}).")
    for region in mapa["modulos"]:
        if (
            region["x"] < 0
            or region["y"] < 0
            or region["x"] + region["ancho"] > ancho
            or (region["y"] + region["alto"] > alto)
        ):
            errors.append(f"la región de {region['modulo']} se sale del lienzo.")

    nodes = Counter(n["compuesto"] for n in mapa["compuestos"])
    for compound, count in nodes.items():
        if count > 1:
            errors.append(f"{compound} está {count} veces en `compuestos`.")
        if compound in cofactors:
            errors.append(
                f"{compound} es un cofactor: se dibuja junto a las flechas, no como nodo."
            )

    for kind, drawn, defined in (
        ("paso", [s["paso"] for s in mapa["pasos"]], [p["id"] for p in via["pasos"]]),
        ("módulo", [m["modulo"] for m in mapa["modulos"]], [m["id"] for m in via["modulos"]]),
    ):
        counts = Counter(drawn)
        for item in defined:
            if counts[item] != 1:
                errors.append(f"el {kind} {item} debe dibujarse una vez (está {counts[item]}).")
        for item in counts.keys() - set(defined):
            errors.append(f"el {kind} {item} no existe en la vía.")

    steps = {p["id"]: p for p in via["pasos"]}
    for arrow in mapa["pasos"]:
        sid = arrow["paso"]
        if sid not in steps:
            continue
        for compound in arrow["desde"] + arrow["hacia"]:
            if compound not in nodes:
                errors.append(f"{sid}: {compound} no está en `compuestos`.")
        if steps[sid]["espontaneo"] and not steps[sid]["reacciones"]:
            continue
        fits = False
        for rid in steps[sid]["reacciones"]:
            reaction = reactions.get(rid)
            if reaction is None:
                errors.append(f"{sid}: {rid} no existe en Rhea.")
                continue
            left = frozenset(c for p in reaction.izquierda for c in p.chebi)
            right = frozenset(c for p in reaction.derecha for c in p.chebi)
            for origin, target in ((left, right), (right, left)):
                if _side_matches(arrow["desde"], origin, ontology) and _side_matches(
                    arrow["hacia"], target, ontology
                ):
                    fits = True
        if not fits:
            errors.append(
                f"{sid}: la flecha {arrow['desde']} -> {arrow['hacia']} no corresponde a lados "
                "opuestos de ninguna reacción Rhea del paso."
            )
    return errors

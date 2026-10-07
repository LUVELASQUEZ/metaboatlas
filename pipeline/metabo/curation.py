"""Curaduría de vías: búsqueda y verificación de IDs contra los datos descargados.

Regla 5 de CLAUDE.md: los IDs Rhea, EC y ChEBI de `curation/vias/*.yaml` no se
escriben de memoria. `search_ec` lista las reacciones Rhea de un número EC para
elegirlas leyendo su ecuación, y `check_via` comprueba cada ID de una vía contra los
archivos de raw/ registrados en el manifiesto.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from metabo.errors import ConfigError
from metabo.manifest import DownloadRecord, Manifest
from metabo.schemas import validation_errors
from metabo.sources import chebi, enzyme, rhea
from metabo.sources.enzyme import EnzymeEntry
from metabo.sources.rhea import Reaction
from metabo.yamlio import load_yaml

# Fuente -> archivos de raw/ que usa la curaduría.
REQUIRED_FILES: dict[str, tuple[str, ...]] = {
    "rhea": ("rhea-directions.tsv", "rhea2ec.tsv", rhea.REACTIONS_FILE),
    "enzyme": ("enzyme.dat",),
    "chebi": ("compounds.tsv.gz",),
}


def _latest_files(manifest: Manifest, fuente: str) -> tuple[str, dict[str, str]]:
    """Versión más reciente descargada de `fuente` y sus archivos (nombre -> ruta en raw/)."""
    records: list[DownloadRecord] = [d for d in manifest.descargas if d.fuente == fuente]
    if not records:
        raise ConfigError(
            f"No hay descargas de {fuente} en raw/manifest.json: "
            f"ejecuta `uv run metabo extraer {fuente}`."
        )
    latest = max(records, key=lambda d: (d.fecha_descarga, d.version))
    files = {Path(d.archivo).name: d.archivo for d in records if d.version == latest.version}
    missing = [name for name in REQUIRED_FILES[fuente] if name not in files]
    if missing:
        raise ConfigError(
            f"La versión {latest.version} de {fuente} no tiene {', '.join(missing)}: "
            f"vuelve a ejecutar `uv run metabo extraer {fuente}`."
        )
    return latest.version, files


@dataclass(frozen=True)
class ReferenceData:
    """Datos descargados con los que se verifica la curaduría."""

    versiones: dict[str, str]
    reacciones: dict[str, Reaction]
    maestras: dict[str, str]
    rhea2ec: dict[str, frozenset[str]]
    enzimas: dict[str, EnzymeEntry]
    compuestos: dict[str, str]

    @classmethod
    def from_raw(cls, raw_dir: Path) -> ReferenceData:
        manifest_path = raw_dir / "manifest.json"
        if not manifest_path.is_file():
            raise ConfigError(
                f"No existe {manifest_path}: descarga primero rhea, enzyme y chebi "
                "con `uv run metabo extraer <fuente>`."
            )
        manifest = Manifest.read(manifest_path)
        versions: dict[str, str] = {}
        paths: dict[str, Path] = {}
        for fuente in REQUIRED_FILES:
            versions[fuente], files = _latest_files(manifest, fuente)
            for name in REQUIRED_FILES[fuente]:
                paths[name] = raw_dir / files[name]
        return cls(
            versiones=versions,
            reacciones=rhea.read_reactions(paths[rhea.REACTIONS_FILE]),
            maestras=rhea.read_masters(paths["rhea-directions.tsv"]),
            rhea2ec=rhea.read_rhea2ec(paths["rhea2ec.tsv"]),
            enzimas=enzyme.read_entries(paths["enzyme.dat"]),
            compuestos=chebi.read_compound_names(paths["compounds.tsv.gz"]),
        )


def search_ec(data: ReferenceData, ec: str) -> list[Reaction]:
    """Reacciones maestras asociadas al número EC (CURIE) en rhea2ec.tsv, ordenadas por ID."""
    found = [
        data.reacciones[rid]
        for rid, ecs in data.rhea2ec.items()
        if ec in ecs and rid in data.reacciones
    ]
    return sorted(found, key=lambda r: int(r.id.split(":")[1]))


def load_via(path: Path) -> dict[str, Any]:
    via = load_yaml(path)
    if not isinstance(via, dict):
        raise ConfigError(f"{path} debe contener un objeto con la definición de la vía.")
    return via


def check_structure(via: dict[str, Any]) -> list[str]:
    """Errores que no dependen de los datos descargados: esquema, módulos y orden."""
    errors = [f"esquema: {e}" for e in validation_errors("via", via)]
    if errors:
        return errors
    steps = [p["id"] for p in via["pasos"]]
    for step, count in Counter(steps).items():
        if count > 1:
            errors.append(f"{step}: el ID de paso está repetido.")
    in_modules = Counter(s for m in via["modulos"] for s in m["pasos"])
    for step in steps:
        if in_modules[step] != 1:
            errors.append(
                f"{step}: debe estar en exactamente un módulo (está en {in_modules[step]})."
            )
    for step in in_modules.keys() - set(steps):
        errors.append(f"{step}: aparece en un módulo pero no está definido en `pasos`.")
    orders = [p["orden"] for p in via["pasos"]]
    if sorted(orders) != list(range(1, len(orders) + 1)):
        errors.append(f"`orden` de los pasos debe ser 1..{len(orders)} sin huecos: {orders}.")
    return errors


def check_via(via: dict[str, Any], data: ReferenceData) -> list[str]:
    """Todos los errores de una vía curada; lista vacía si cada ID se verificó."""
    errors = check_structure(via)
    if errors:
        return errors

    for fuente, version in data.versiones.items():
        curated = via["fuentes"].get(fuente)
        if curated != version:
            errors.append(
                f"fuentes.{fuente}: la vía dice {curated!r} y la versión descargada es "
                f"{version!r}; vuelve a verificar la vía y actualiza la versión."
            )

    for step in via["pasos"]:
        sid = step["id"]
        step_ec = set(step["ec"])
        for ec in step["ec"]:
            entry = data.enzimas.get(ec)
            if entry is None:
                errors.append(f"{sid}: {ec} no existe en enzyme.dat.")
            elif entry.eliminada:
                errors.append(f"{sid}: {ec} está eliminado en ENZYME.")
            elif entry.transferida_a:
                targets = ", ".join(entry.transferida_a)
                errors.append(f"{sid}: {ec} fue transferido en ENZYME a {targets}.")
        for rid in step["reacciones"]:
            reaction = data.reacciones.get(rid)
            if reaction is None:
                errors.append(f"{sid}: {rid} no existe en Rhea.")
                continue
            master = data.maestras.get(rid)
            if master != rid:
                errors.append(f"{sid}: {rid} no es una reacción maestra; usa {master}.")
            linked = data.rhea2ec.get(rid, frozenset())
            if not linked & step_ec:
                shown = ", ".join(sorted(linked)) or "ninguno"
                errors.append(
                    f"{sid}: {rid} no está asociado en rhea2ec a ningún EC del paso "
                    f"(está asociado a: {shown})."
                )
            for compound in sorted(reaction.chebi):
                if compound not in data.compuestos:
                    errors.append(f"{sid}: {compound} (participante de {rid}) no existe en ChEBI.")
    return errors

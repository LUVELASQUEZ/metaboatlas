"""Línea de comandos `metabo` (sección 6 de docs/MANUAL.md)."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from metabo import __version__
from metabo.config import load_config
from metabo.errors import PipelineError
from metabo.organisms import load_organisms
from metabo.registry import SourceRegistry

# Etapas de `metabo build`, en orden. Se implementan en tareas posteriores.
STAGES: tuple[tuple[str, str], ...] = (
    ("extraer", "descarga de las fuentes verificadas a raw/ con su manifiesto"),
    ("cargar", "carga de los archivos crudos en DuckDB"),
    ("normalizar", "identificadores CURIE, Rhea maestro y reconciliación de compuestos"),
    ("integrar", "lectura de la curaduría de curation/vias/"),
    ("enriquecer", "nombres en español, bibliografía y linaje"),
    ("calcular", "cobertura de cada vía en cada organismo"),
    ("validar", "esquemas, integridad referencial y verdades biológicas"),
    ("exportar", "JSON por entidad, índices y manifest.json"),
    ("publicar", "GitHub Release data-AAAA.MM"),
)


def _load_all() -> tuple[SourceRegistry, int]:
    load_config()
    registry = SourceRegistry.load()
    organisms = load_organisms()
    return registry, len(organisms)


def cmd_validate(_: argparse.Namespace) -> int:
    registry, n_organisms = _load_all()
    n_sources = sum(1 for _ in registry)
    print(
        f"OK: config.yaml, organismos.yaml ({n_organisms} organismos) "
        f"y sources.yaml ({n_sources} fuentes) son válidos."
    )
    return 0


def cmd_fuentes(_: argparse.Namespace) -> int:
    registry = SourceRegistry.load()
    for source in registry:
        mark = "descargable" if source.downloadable else "no descargable"
        print(f"{source.key:<16} {source.uso:<14} {source.estado:<24} {mark}")
    return 0


def cmd_build(_: argparse.Namespace) -> int:
    registry, n_organisms = _load_all()
    downloadable = [s.nombre for s in registry if s.downloadable]
    print(f"MetaboAtlas pipeline {__version__} · {n_organisms} organismos")
    if downloadable:
        print("Fuentes descargables: " + ", ".join(downloadable))
    else:
        print("Ninguna fuente está verificada en sources.yaml: no se descargará nada.")
    for number, (name, description) in enumerate(STAGES, start=1):
        print(f"  {number}. {name:<11} pendiente — {description}")
    print("El esqueleto funciona; las etapas se implementan en las próximas tareas.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="metabo", description="Pipeline de MetaboAtlas.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build", help="reconstruye el paquete de datos").set_defaults(func=cmd_build)
    sub.add_parser(
        "validate", help="valida config.yaml, organismos.yaml y sources.yaml"
    ).set_defaults(func=cmd_validate)
    sub.add_parser("fuentes", help="lista las fuentes y si se pueden descargar").set_defaults(
        func=cmd_fuentes
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except PipelineError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""Línea de comandos `metabo` (sección 6 de docs/MANUAL.md)."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from collections.abc import Callable, Sequence
from datetime import date
from pathlib import Path

from metabo import __version__, curation, maps
from metabo.config import load_config
from metabo.coverage import compute
from metabo.download import Downloader
from metabo.errors import PipelineError
from metabo.export import compounds as export_compounds
from metabo.export import names as export_names
from metabo.export import package
from metabo.export import references as export_references
from metabo.export.attribution import attribution
from metabo.manifest import DownloadRecord, Manifest
from metabo.organisms import load_organisms
from metabo.paths import repo_root
from metabo.registry import SourceRegistry
from metabo.sources import chebi, enzyme, europe_pmc, ncbi_taxonomy, rhea, uniprot, wikidata

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


def _extract_wikidata(downloader: Downloader, raw_dir: Path) -> tuple[str, list[DownloadRecord]]:
    """Consulta en Wikidata los nombres de los compuestos y las enzimas del paquete.

    Los IDs salen de las vías curadas, sus mapas y las reacciones de Rhea ya
    descargadas, así que Rhea debe extraerse antes.
    """
    root = repo_root()
    compounds, ecs = package.entity_ids(raw_dir, _curated_vias(root, []), _curated_maps(root))
    return wikidata.extract(downloader, raw_dir, compounds, ecs)


def _extract_europe_pmc(downloader: Downloader, raw_dir: Path) -> tuple[str, list[DownloadRecord]]:
    """Consulta en Europe PMC los datos de cita de curation/referencias.yaml."""
    references = export_references.load_curation(repo_root() / "curation" / "referencias.yaml")
    return europe_pmc.extract(downloader, raw_dir, [r.pmid for r in references])


# Extractores disponibles: fuente -> función que descarga a raw/ y devuelve sus registros.
EXTRACTORS: dict[str, Callable[[Downloader, Path], tuple[object, list[DownloadRecord]]]] = {
    "chebi": chebi.extract,
    "enzyme": enzyme.extract,
    "europe_pmc": _extract_europe_pmc,
    "ncbi_taxonomy": ncbi_taxonomy.extract,
    "rhea": rhea.extract,
    "uniprot": uniprot.extract,
    "wikidata": _extract_wikidata,
}


def cmd_extraer(args: argparse.Namespace) -> int:
    config = load_config()
    registry = SourceRegistry.load()
    raw_dir = repo_root() / config.directorios.crudos
    downloader = Downloader(config.descargas, registry, raw_dir)
    _, records = EXTRACTORS[args.fuente](downloader, raw_dir)

    manifest_path = raw_dir / "manifest.json"
    if manifest_path.exists():
        manifest = Manifest.read(manifest_path)
    else:
        manifest = Manifest(version_datos=date.today().strftime("%Y.%m"))
    for record in records:
        manifest.add(record)
    manifest.write(manifest_path)

    print(f"{registry.get(args.fuente).nombre}: versión {records[0].version}")
    for record in records:
        print(f"  {record.archivo}  {record.bytes} bytes  sha256 {record.sha256}")
    print(f"Manifiesto actualizado: {manifest_path}")
    return 0


def _reference_data() -> curation.ReferenceData:
    config = load_config()
    return curation.ReferenceData.from_raw(repo_root() / config.directorios.crudos)


def cmd_curar_buscar(args: argparse.Namespace) -> int:
    ec = args.ec if args.ec.startswith("EC:") else f"EC:{args.ec}"
    data = _reference_data()
    entry = data.enzimas.get(ec)
    if entry is None:
        print(f"{ec} no existe en enzyme.dat (ENZYME {data.versiones['enzyme']}).")
    else:
        estado = "vigente" if entry.vigente else "NO VIGENTE"
        print(f"{ec}  {entry.nombre}  ({estado}, ENZYME {data.versiones['enzyme']})")
    reactions = curation.search_ec(data, ec)
    print(
        f"Reacciones maestras de Rhea {data.versiones['rhea']} asociadas a {ec}: {len(reactions)}"
    )
    for reaction in reactions:
        print(f"  {reaction.id}  {reaction.definicion}")
        participants = ", ".join(
            f"{c} ({data.compuestos.get(c, '¿no está en ChEBI?')})" for c in sorted(reaction.chebi)
        )
        print(f"      {participants}")
    return 0


def cmd_curar_validar(args: argparse.Namespace) -> int:
    paths = [Path(p) for p in args.archivos] or sorted(
        (repo_root() / "curation" / "vias").glob("*.yaml")
    )
    if not paths:
        print("No hay vías en curation/vias/.")
        return 0
    data = _reference_data()
    failed = 0
    for path in paths:
        errors = curation.check_via(curation.load_via(path), data)
        if errors:
            failed += 1
            print(f"ERROR {path.name}:")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"OK {path.name}")
    versions = ", ".join(f"{k} {v}" for k, v in data.versiones.items())
    print(f"Verificado contra: {versions}")
    return 1 if failed else 0


def cmd_cobertura(args: argparse.Namespace) -> int:
    config = load_config()
    root = repo_root()
    raw_dir = root / config.directorios.crudos
    organisms = load_organisms()
    if args.taxon:
        organisms = [o for o in organisms if o.id in args.taxon]
        unknown = set(args.taxon) - {o.id for o in organisms}
        if unknown:
            print(f"No están en organismos.yaml: {', '.join(sorted(unknown))}", file=sys.stderr)
            return 1
    skipped = [o for o in organisms if o.proteoma_referencia is None]
    organisms = [o for o in organisms if o.proteoma_referencia is not None]
    vias = _curated_vias(root, args.vias)

    inputs = compute.CoverageInputs.from_raw(raw_dir, organisms)
    documents = compute.compute_all(
        vias, organisms, inputs, compute.thresholds(config.cobertura.umbrales), date.today()
    )
    version_datos = Manifest.read(raw_dir / "manifest.json").version_datos
    out_dir = root / config.directorios.salida / version_datos
    written = compute.write_documents(documents, out_dir)

    names = {o.id: o.nombre for o in organisms}
    for document in documents:
        counts = Counter(p["estado"] for p in document["pasos"].values())
        detail = ", ".join(f"{k} {v}" for k, v in sorted(counts.items()))
        print(
            f"{document['via']:<20} {names[document['taxon']]:<32} "
            f"{document['cobertura']:>5} %  {document['clase']:<14} ({detail})"
        )
    for organism in skipped:
        print(f"Sin proteoma de referencia, se omite: {organism.id} {organism.nombre}")
    versions = ", ".join(f"{k} {v}" for k, v in inputs.versiones.items())
    print(f"{len(written)} archivos en {out_dir / 'cobertura'} (calculado con {versions})")
    return 0


def _curated_vias(root: Path, given: Sequence[str]) -> list[dict]:
    paths = [Path(p) for p in given] or sorted((root / "curation" / "vias").glob("*.yaml"))
    vias = [curation.load_via(path) for path in paths]
    for via, path in zip(vias, paths, strict=True):
        errors = curation.check_structure(via)
        if errors:
            raise PipelineError(f"{path.name} no es válida: " + "; ".join(errors))
    return vias


def _curated_maps(root: Path) -> dict[str, dict]:
    return {
        path.stem: maps.load_map(path)
        for path in sorted((root / "curation" / "mapas").glob("*.json"))
    }


def cmd_exportar(args: argparse.Namespace) -> int:
    config = load_config()
    root = repo_root()
    raw_dir = root / config.directorios.crudos
    organisms = load_organisms()
    built = package.build(
        raw_dir,
        _curated_vias(root, []),
        organisms,
        export_compounds.load_curation(root / "curation" / "compuestos.yaml"),
        compute.thresholds(config.cobertura.umbrales),
        date.today(),
        _curated_maps(root),
        export_names.load_curation(root / "curation" / "nombres_es.yaml"),
        export_references.load_curation(root / "curation" / "referencias.yaml"),
    )
    out_dir = root / config.directorios.salida / built.manifest.version_datos
    written = built.write(out_dir)
    (out_dir / "ATRIBUCION.md").write_text(
        attribution(built.manifest, SourceRegistry.load()), encoding="utf-8"
    )
    folders = Counter(
        p.parent.relative_to(out_dir).parts[0] for p in written if p.parent != out_dir
    )
    print(f"Paquete de datos {built.manifest.version_datos} en {out_dir}:")
    for folder, count in sorted(folders.items()):
        print(f"  {folder:<12} {count} archivos")
    versions = ", ".join(sorted({f"{d.fuente} {d.version}" for d in built.manifest.descargas}))
    print(f"  manifest.json  ({versions})")
    print("  ATRIBUCION.md  (licencias y citas de las fuentes)")
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
    extraer = sub.add_parser(
        "extraer", help="descarga una fuente verificada a raw/ y actualiza el manifiesto"
    )
    extraer.add_argument("fuente", choices=sorted(EXTRACTORS))
    extraer.set_defaults(func=cmd_extraer)
    curar = sub.add_parser(
        "curar", help="ayudas para curar vías con los datos descargados en raw/"
    ).add_subparsers(dest="accion", required=True)
    buscar = curar.add_parser("buscar", help="lista las reacciones Rhea de un número EC")
    buscar.add_argument("ec", help="número EC, p. ej. 2.7.1.1 o EC:2.7.1.1")
    buscar.set_defaults(func=cmd_curar_buscar)
    validar = curar.add_parser(
        "validar", help="verifica los IDs Rhea, EC y ChEBI de las vías de curation/vias/"
    )
    validar.add_argument("archivos", nargs="*", help="vías a verificar (por defecto, todas)")
    validar.set_defaults(func=cmd_curar_validar)
    cobertura = sub.add_parser(
        "cobertura", help="calcula la cobertura de cada vía curada en cada organismo"
    )
    cobertura.add_argument("vias", nargs="*", help="vías de curation/vias/ (por defecto, todas)")
    cobertura.add_argument(
        "--taxon", action="append", help="solo este organismo (p. ej. taxon:511145); repetible"
    )
    cobertura.set_defaults(func=cmd_cobertura)
    sub.add_parser(
        "exportar", help="escribe el paquete de datos data/<version>/ validado contra schema/"
    ).set_defaults(func=cmd_exportar)
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

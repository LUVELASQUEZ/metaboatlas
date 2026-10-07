"""Paquete de datos `data/<version_datos>/` (secciones 4 y 6 de docs/MANUAL.md).

Exporta solo las entidades que tocan las vías curadas: las vías, sus reacciones, los
compuestos de esas reacciones, las enzimas (EC) de sus pasos, los organismos de
organismos.yaml y la cobertura de cada vía en cada organismo. Cada documento se
valida contra su esquema de schema/ y lleva la procedencia de cada dato (fuente, ID,
versión y fecha de descarga). `manifest.json` lista las descargas usadas.

Lo que todavía no tiene fuente queda vacío o en null, nunca inventado:
- SMILES, InChI e InChIKey: falta descargar structures.tsv.gz de ChEBI.
- Nombres en español (`nombre.es`): vendrán de Wikidata.
- Referencias cruzadas de compuestos y reacciones: falta reference.tsv.gz de ChEBI.
- Reversibilidad y ΔG de las reacciones, y tinción de Gram: sin fuente verificada.
"""

from __future__ import annotations

import json
import shutil
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from metabo import schemas
from metabo.coverage import compute
from metabo.coverage.algorithm import Thresholds
from metabo.errors import ConfigError
from metabo.export.compounds import Classifier, CompoundCuration, check_names
from metabo.manifest import DownloadRecord, Manifest
from metabo.organisms import Organism
from metabo.sources import chebi, enzyme, ncbi_taxonomy, rhea, uniprot

# Fuente -> archivos de raw/ que usa la exportación (además de los proteomas).
REQUIRED_FILES: dict[str, tuple[str, ...]] = {
    "rhea": ("rhea-directions.tsv", "rhea2ec.tsv", rhea.REACTIONS_FILE),
    "chebi": (
        "compounds.tsv.gz",
        "chemical_data.tsv.gz",
        "names.tsv.gz",
        "relation.tsv.gz",
        "relation_type.tsv.gz",
    ),
    "enzyme": ("enzyme.dat",),
    "ncbi_taxonomy": (ncbi_taxonomy.ARCHIVE,),
}


@dataclass(frozen=True)
class SourceFiles:
    """Versión usada de una fuente, sus archivos y sus registros del manifiesto."""

    version: str
    paths: dict[str, Path]
    records: tuple[DownloadRecord, ...]

    def procedencia(self, fuente: str, native_id: str, archivo: str) -> dict[str, str]:
        record = next(r for r in self.records if Path(r.archivo).name == archivo)
        return {
            "fuente": fuente,
            "id": native_id,
            "version": self.version,
            "fecha_descarga": record.fecha_descarga,
        }


def _source(manifest: Manifest, raw_dir: Path, fuente: str, required: Sequence[str]) -> SourceFiles:
    version, files = manifest.latest(fuente, required)
    records = tuple(d for d in manifest.descargas if d.fuente == fuente and d.version == version)
    return SourceFiles(version, {name: raw_dir / path for name, path in files.items()}, records)


def _native(curie: str) -> str:
    return curie.split(":", 1)[1]


def file_name(curie: str) -> str:
    """Nombre de archivo de un ID: `:` se reemplaza por `_` (CLAUDE.md)."""
    return curie.replace(":", "_") + ".json"


@dataclass
class Package:
    """Documentos del paquete por ruta relativa, y las descargas que se usaron."""

    documents: dict[str, dict[str, Any]]
    manifest: Manifest

    def write(self, out_dir: Path) -> list[Path]:
        """Escribe el paquete en `out_dir`, reemplazando una exportación anterior."""
        if out_dir.exists():
            shutil.rmtree(out_dir)
        written = []
        for relative, document in sorted(self.documents.items()):
            path = out_dir / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", "utf-8")
            written.append(path)
        self.manifest.write(out_dir / "manifest.json")
        written.append(out_dir / "manifest.json")
        return written


DIRECTION_KEYS = ("izquierda_a_derecha", "derecha_a_izquierda", "bidireccional")


def _reaction_document(
    reaction: rhea.Reaction,
    directions: tuple[str, str, str],
    ecs: Iterable[str],
    source: SourceFiles,
) -> dict[str, Any]:
    participants = [
        {"compuesto": compound, "lado": lado, "estequiometria": participant.coeficiente}
        for lado, side in (("izquierda", reaction.izquierda), ("derecha", reaction.derecha))
        for participant in side
        for compound in participant.chebi
    ]
    return {
        "id": reaction.id,
        "ecuacion": reaction.definicion,
        "participantes": participants,
        "direcciones": dict(
            zip(
                ("izquierda_a_derecha", "derecha_a_izquierda", "bidireccional"),
                directions,
                strict=True,
            )
        ),
        "reversible": None,
        # Rhea marca los compartimentos de una reacción de transporte en su ecuación:
        # "sulfate(out) + ATP + H2O = sulfate(in) + …".
        "es_transporte": "(in)" in reaction.definicion or "(out)" in reaction.definicion,
        "ec": sorted(ecs, key=_ec_key),
        "delta_g": None,
        "xrefs": [],
        "procedencia": [source.procedencia("rhea", _native(reaction.id), rhea.REACTIONS_FILE)],
    }


def _ec_key(ec: str) -> tuple[int | str, ...]:
    return tuple(int(p) if p.isdigit() else p for p in _native(ec).split("."))


def _compound_document(
    compound: chebi.Compound, classifier: Classifier, source: SourceFiles
) -> dict[str, Any]:
    clase, cofactor = classifier.classify(compound.id)
    return {
        "id": compound.id,
        "nombre": {"es": None, "en": compound.nombre},
        "definicion": compound.definicion,
        "sinonimos": list(compound.sinonimos),
        "formula": compound.formula,
        "carga": compound.carga,
        "masa_monoisotopica": compound.masa_monoisotopica,
        "smiles": None,
        "inchi": None,
        "inchikey": None,
        "clase": clase,
        "es_cofactor": cofactor,
        "xrefs": [],
        "procedencia": [source.procedencia("chebi", _native(compound.id), "compounds.tsv.gz")],
    }


def _protein_document(
    entry: uniprot.Entry, taxon: str, source: SourceFiles, archivo: str
) -> dict[str, Any]:
    return {
        "id": f"UNIPROT:{entry.accession}",
        "taxon": taxon,
        "nombre": entry.nombre,
        "genes": list(entry.genes),
        "ec": sorted(set(entry.ec), key=_ec_key),
        "rhea": sorted(set(entry.rhea), key=lambda r: int(_native(r))),
        "revisada": entry.revisada,
        "puntaje_anotacion": entry.puntaje_anotacion,
        "procedencia": [source.procedencia("uniprot", entry.accession, archivo)],
    }


def _enzyme_document(
    entry: enzyme.EnzymeEntry,
    reactions: Iterable[str],
    proteins: list[dict[str, Any]],
    source: SourceFiles,
) -> dict[str, Any]:
    estado = "eliminado" if entry.eliminada else "transferido" if entry.transferida_a else "vigente"
    document: dict[str, Any] = {
        "id": entry.ec,
        "nombre": {"es": None, "en": entry.nombre},
        "nombres_alternativos": list(dict.fromkeys(entry.nombres_alternativos)),
        "clase": int(_native(entry.ec).split(".")[0]),
        "reaccion": entry.reaccion,
        "cofactores": list(entry.cofactores),
        "estado": estado,
        "reacciones": sorted(reactions, key=lambda r: int(_native(r))),
        "proteinas": proteins,
        # El número EC es el ID de la entrada en ENZYME y en KEGG (KEGG: solo enlace).
        "xrefs": [
            {"fuente": "enzyme", "tipo": "enzima", "id": _native(entry.ec)},
            {"fuente": "kegg", "tipo": "enzima", "id": _native(entry.ec)},
        ],
        "procedencia": [source.procedencia("enzyme", _native(entry.ec), "enzyme.dat")],
    }
    if entry.transferida_a:
        document["transferido_a"] = list(entry.transferida_a)
    return document


def _kegg_code(entries: Iterable[uniprot.Entry]) -> str | None:
    """Prefijo de organismo más frecuente en las referencias KEGG de UniProt ("eco")."""
    counts = Counter(ref.split(":", 1)[0] for entry in entries for ref in entry.kegg if ":" in ref)
    return counts.most_common(1)[0][0] if counts else None


def _organism_document(
    organism: Organism,
    record: ncbi_taxonomy.TaxonRecord,
    kegg_code: str | None,
    taxonomy: SourceFiles,
    proteomes: SourceFiles,
) -> dict[str, Any]:
    proteome = organism.proteoma_referencia
    return {
        "id": organism.id,
        "nombre_cientifico": record.nombre_cientifico,
        "cepa": None,
        "nombre_comun": ({"es": None, "en": record.nombre_comun} if record.nombre_comun else None),
        "rango": record.rango,
        "linaje": [{"taxon": n.taxon, "nombre": n.nombre, "rango": n.rango} for n in record.linaje],
        "dominio": record.dominio,
        "gram": None if record.dominio == "bacteria" else "no_aplica",
        "proteoma_referencia": organism.proteoma_referencia,
        "intereses": list(organism.intereses),
        "codigo_kegg": kegg_code,
        "xrefs": [
            {"fuente": "ncbi_taxonomy", "tipo": "organismo", "id": organism.taxon_id},
        ],
        "procedencia": [
            taxonomy.procedencia("ncbi_taxonomy", organism.taxon_id, ncbi_taxonomy.ARCHIVE),
            proteomes.procedencia("uniprot", str(proteome), f"{proteome}.tsv.gz"),
        ],
    }


def build(
    raw_dir: Path,
    vias: Sequence[Mapping[str, Any]],
    organisms: Sequence[Organism],
    compound_curation: CompoundCuration,
    umbrales: Thresholds,
    calculado: date,
) -> Package:
    """Arma todos los documentos del paquete y los valida contra schema/."""
    manifest = Manifest.read(raw_dir / "manifest.json")
    without = [o.id for o in organisms if o.proteoma_referencia is None]
    if without:
        raise ConfigError(f"Sin proteoma de referencia en organismos.yaml: {', '.join(without)}.")
    sources = {f: _source(manifest, raw_dir, f, names) for f, names in REQUIRED_FILES.items()}
    proteome_files = [f"{o.proteoma_referencia}.tsv.gz" for o in organisms]
    sources["uniprot"] = _source(manifest, raw_dir, "uniprot", proteome_files)
    documents: dict[str, dict[str, Any]] = {}

    # Vías curadas.
    for via in vias:
        documents[f"vias/{_native(via['id'])}.json"] = dict(via)

    # Reacciones de los pasos.
    rhea_files = sources["rhea"].paths
    all_reactions = rhea.read_reactions(rhea_files[rhea.REACTIONS_FILE])
    directions = rhea.read_directions(rhea_files["rhea-directions.tsv"])
    rhea2ec = rhea.read_rhea2ec(rhea_files["rhea2ec.tsv"])
    reaction_ids = sorted(
        {r for via in vias for p in via["pasos"] for r in p["reacciones"]},
        key=lambda r: int(_native(r)),
    )
    for rid in reaction_ids:
        if rid not in all_reactions or rid not in directions:
            raise ConfigError(
                f"{rid} no es una reacción maestra de Rhea {sources['rhea'].version}."
            )
        documents[f"reacciones/{file_name(rid)}"] = _reaction_document(
            all_reactions[rid], directions[rid], rhea2ec.get(rid, ()), sources["rhea"]
        )

    # Compuestos de esas reacciones, con su clase.
    compound_ids = {c for rid in reaction_ids for c in all_reactions[rid].chebi}
    curated_ids = {node.id for node in compound_curation.nodes}
    chebi_files = sources["chebi"].paths
    compounds = chebi.read_compounds(chebi_files, compound_ids | curated_ids)
    errors = check_names(compound_curation, {k: c.nombre for k, c in compounds.items()})
    if errors:
        raise ConfigError(
            "curation/compuestos.yaml no coincide con ChEBI:\n  " + "\n  ".join(errors)
        )
    classifier = Classifier(
        compound_curation,
        chebi.read_ontology(chebi_files["relation.tsv.gz"], chebi_files["relation_type.tsv.gz"]),
    )
    for cid in sorted(compound_ids, key=lambda c: int(_native(c))):
        documents[f"compuestos/{file_name(cid)}"] = _compound_document(
            compounds[cid], classifier, sources["chebi"]
        )

    # Proteínas de los proteomas; organismos.
    entries: dict[str, list[uniprot.Entry]] = {}
    for organism, archivo in zip(organisms, proteome_files, strict=True):
        entries[organism.id] = list(uniprot.read_entries(sources["uniprot"].paths[archivo]))
    taxa = ncbi_taxonomy.read_taxa(
        sources["ncbi_taxonomy"].paths[ncbi_taxonomy.ARCHIVE], [o.id for o in organisms]
    )
    for organism in organisms:
        documents[f"organismos/{organism.taxon_id}.json"] = _organism_document(
            organism,
            taxa[organism.id],
            _kegg_code(entries[organism.id]),
            sources["ncbi_taxonomy"],
            sources["uniprot"],
        )

    # Enzimas (EC) de los pasos, con las proteínas que las tienen en cada organismo.
    enzymes = enzyme.read_entries(sources["enzyme"].paths["enzyme.dat"])
    ec_ids = sorted({ec for via in vias for p in via["pasos"] for ec in p["ec"]}, key=_ec_key)
    ec_reactions: dict[str, set[str]] = {}
    for rid, ecs in rhea2ec.items():
        for ec in ecs:
            ec_reactions.setdefault(ec, set()).add(rid)
    for ec in ec_ids:
        if ec not in enzymes:
            raise ConfigError(f"{ec} no existe en ENZYME {sources['enzyme'].version}.")
        proteins = [
            _protein_document(entry, organism.id, sources["uniprot"], archivo)
            for organism, archivo in zip(organisms, proteome_files, strict=True)
            for entry in entries[organism.id]
            if ec in entry.ec
        ]
        documents[f"enzimas/{file_name(ec)}"] = _enzyme_document(
            enzymes[ec], ec_reactions.get(ec, ()), proteins, sources["enzyme"]
        )

    # Cobertura de cada vía en cada organismo.
    inputs = compute.CoverageInputs.from_raw(raw_dir, organisms)
    for document in compute.compute_all(vias, organisms, inputs, umbrales, calculado):
        relative = compute.output_path(Path("."), document).as_posix()
        documents[relative] = document

    for relative, document in documents.items():
        schema = _SCHEMA_BY_FOLDER[relative.split("/", 1)[0]]
        schemas.validate(schema, document, label=relative)

    used = Manifest(version_datos=manifest.version_datos)
    for source in sources.values():
        for record in source.records:
            used.add(record)
    return Package(documents, used)


_SCHEMA_BY_FOLDER = {
    "vias": "via",
    "reacciones": "reaccion",
    "compuestos": "compuesto",
    "enzimas": "enzima",
    "organismos": "organismo",
    "cobertura": "cobertura",
}

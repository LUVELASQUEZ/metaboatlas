"""Nombres en español del paquete: curaduría manual primero, Wikidata después.

curation/nombres_es.yaml asigna un nombre en español a un ID y repite el nombre que
ese ID tiene en su fuente (`en`), que se comprueba contra los datos descargados. Si
un ID no está curado, se usa su etiqueta de Wikidata cuando es única; si no hay
ninguna, `nombre.es` queda en null (marcado para traducción manual).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from metabo.errors import ConfigError
from metabo.sources.wikidata import Label

SECCIONES = ("compuestos", "enzimas", "organismos")


@dataclass(frozen=True)
class CuratedName:
    en: str
    es: str


@dataclass(frozen=True)
class NameCuration:
    """Nombres curados por sección (compuestos, enzimas, organismos) e ID."""

    secciones: dict[str, dict[str, CuratedName]] = field(default_factory=dict)

    def get(self, seccion: str, curie: str) -> CuratedName | None:
        return self.secciones.get(seccion, {}).get(curie)


def load_curation(path: Path) -> NameCuration:
    if not path.exists():
        return NameCuration()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    unknown = set(data) - set(SECCIONES)
    if unknown:
        raise ConfigError(f"{path.name}: secciones desconocidas {', '.join(sorted(unknown))}.")
    secciones: dict[str, dict[str, CuratedName]] = {}
    for seccion in SECCIONES:
        entries = {}
        for curie, entry in (data.get(seccion) or {}).items():
            if not isinstance(entry, dict) or set(entry) != {"en", "es"}:
                raise ConfigError(f"{path.name}: {curie} debe tener solo `en` y `es`.")
            en, es = str(entry["en"]).strip(), str(entry["es"]).strip()
            if not en or not es:
                raise ConfigError(f"{path.name}: {curie} tiene un nombre vacío.")
            entries[str(curie)] = CuratedName(en=en, es=es)
        secciones[seccion] = entries
    return NameCuration(secciones)


def check_names(curation: NameCuration, seccion: str, names: Mapping[str, str | None]) -> list[str]:
    """Errores si un ID curado que se exporta no tiene en la fuente el nombre `en` curado.

    `names` es ID -> nombre en la fuente de las entidades del paquete; los IDs curados
    que no se exportan se ignoran (pueden ser de vías todavía no curadas).
    """
    errors = []
    for curie, entry in sorted(curation.secciones.get(seccion, {}).items()):
        if curie in names and names[curie] != entry.en:
            errors.append(
                f"{seccion} {curie}: el nombre curado es '{entry.en}', "
                f"pero la fuente dice '{names[curie]}'."
            )
    return errors


@dataclass(frozen=True)
class SpanishName:
    """Nombre en español elegido y de dónde sale (None si no hay ninguno)."""

    es: str | None
    origen: str | None
    wikidata: str | None = None


def resolve(
    curation: NameCuration, seccion: str, curie: str, wikidata: Mapping[str, Label]
) -> SpanishName:
    curated = curation.get(seccion, curie)
    if curated is not None:
        return SpanishName(es=curated.es, origen="curaduria")
    label = wikidata.get(curie)
    if label is not None:
        return SpanishName(es=label.es, origen="wikidata", wikidata=label.qid)
    return SpanishName(es=None, origen=None)

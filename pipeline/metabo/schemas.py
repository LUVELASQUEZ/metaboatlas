"""Validación contra los JSON Schema de schema/ (contrato entre pipeline y web)."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from metabo.errors import ConfigError
from metabo.paths import schema_dir


@cache
def _validators(directory: Path) -> dict[str, Draft202012Validator]:
    schemas = {
        path.name.removesuffix(".schema.json"): json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(directory.glob("*.schema.json"))
    }
    if not schemas:
        raise ConfigError(f"No hay esquemas en {directory}.")
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas.values()
    )
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
    return {
        name: Draft202012Validator(schema, registry=registry) for name, schema in schemas.items()
    }


def schema_names() -> list[str]:
    return sorted(_validators(schema_dir()))


def validation_errors(name: str, instance: Any) -> list[str]:
    """Lista legible de errores de `instance` contra el esquema `name` (vacía si es válido)."""
    validators = _validators(schema_dir())
    if name not in validators:
        raise ConfigError(f"No existe el esquema '{name}' en {schema_dir()}.")
    errors = []
    for error in validators[name].iter_errors(instance):
        location = "/".join(str(part) for part in error.absolute_path) or "(raíz)"
        errors.append(f"{location}: {error.message}")
    return errors


def validate(name: str, instance: Any, label: str) -> None:
    """Lanza ConfigError si `instance` no cumple el esquema `name`."""
    errors = validation_errors(name, instance)
    if errors:
        detail = "\n".join(f"  - {error}" for error in errors)
        raise ConfigError(f"{label} no cumple schema/{name}.schema.json:\n{detail}")

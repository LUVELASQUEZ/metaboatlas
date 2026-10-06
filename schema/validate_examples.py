# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema>=4.23", "referencing>=0.35", "pyyaml>=6"]
# ///
"""Validate the JSON Schemas in schema/ and their examples.

Checks:
1. Every *.schema.json is a valid Draft 2020-12 schema.
2. Every file in ejemplos/validos/<schema>.json passes its schema.
3. Every file in ejemplos/invalidos/<schema>--<reason>.json fails its schema.
4. sources.yaml passes fuentes.schema.json.

Usage (from the repository root):
    uv run schema/validate_examples.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

SCHEMA_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCHEMA_DIR.parent
EXAMPLES_DIR = SCHEMA_DIR / "ejemplos"


def load_schemas() -> dict[str, dict]:
    """Return schemas keyed by short name (via, paso, …)."""
    return {
        path.name.removesuffix(".schema.json"): json.loads(
            path.read_text(encoding="utf-8")
        )
        for path in sorted(SCHEMA_DIR.glob("*.schema.json"))
    }


def build_registry(schemas: dict[str, dict]) -> Registry:
    resources = [
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas.values()
    ]
    return Registry().with_resources(resources)


def schema_name_for(example: Path) -> str:
    return example.stem.split("--", 1)[0]


def main() -> int:
    schemas = load_schemas()
    registry = build_registry(schemas)
    validators = {
        name: Draft202012Validator(schema, registry=registry)
        for name, schema in schemas.items()
    }
    errors: list[str] = []

    for name, schema in schemas.items():
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:  # noqa: BLE001 - report every problem
            errors.append(f"[esquema] {name}: {exc}")

    for example in sorted((EXAMPLES_DIR / "validos").glob("*.json")):
        name = schema_name_for(example)
        if name not in validators:
            errors.append(f"[válido] {example.name}: no existe el esquema '{name}'")
            continue
        instance = json.loads(example.read_text(encoding="utf-8"))
        for error in validators[name].iter_errors(instance):
            path = "/".join(str(p) for p in error.absolute_path)
            errors.append(f"[válido] {example.name} en '{path}': {error.message}")

    for example in sorted((EXAMPLES_DIR / "invalidos").glob("*.json")):
        name = schema_name_for(example)
        if name not in validators:
            errors.append(f"[inválido] {example.name}: no existe el esquema '{name}'")
            continue
        instance = json.loads(example.read_text(encoding="utf-8"))
        if validators[name].is_valid(instance):
            errors.append(f"[inválido] {example.name}: debería fallar y pasó")

    sources = yaml.safe_load((REPO_ROOT / "sources.yaml").read_text(encoding="utf-8"))
    for error in validators["fuentes"].iter_errors(sources):
        path = "/".join(str(p) for p in error.absolute_path)
        errors.append(f"[sources.yaml] en '{path}': {error.message}")

    if errors:
        print("\n".join(errors))
        print(f"\n{len(errors)} error(es).")
        return 1

    print(
        f"OK: {len(schemas)} esquemas, "
        f"{len(list((EXAMPLES_DIR / 'validos').glob('*.json')))} ejemplos válidos, "
        f"{len(list((EXAMPLES_DIR / 'invalidos').glob('*.json')))} ejemplos inválidos "
        "y sources.yaml."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Rutas del repositorio que comparte el pipeline."""

from __future__ import annotations

import os
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent.parent


def repo_root() -> Path:
    """Raíz del repositorio. Se puede cambiar con METABO_ROOT (útil en pruebas)."""
    override = os.environ.get("METABO_ROOT")
    return Path(override).resolve() if override else PIPELINE_DIR.parent


def schema_dir() -> Path:
    return repo_root() / "schema"

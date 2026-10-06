"""Lectura de archivos YAML con errores claros."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from metabo.errors import ConfigError


def load_yaml(path: Path) -> Any:
    if not path.is_file():
        raise ConfigError(f"No existe el archivo {path}.")
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path} no es un YAML válido: {exc}") from exc

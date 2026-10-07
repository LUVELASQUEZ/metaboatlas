"""Configuración del pipeline (pipeline/config.yaml)."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from metabo.errors import ConfigError
from metabo.paths import PIPELINE_DIR
from metabo.yamlio import load_yaml

DEFAULT_CONFIG_PATH = PIPELINE_DIR / "config.yaml"

# El correo de contacto no se guarda en el repositorio (es público): se lee de
# esta variable de entorno, que en GitHub Actions viene de un secreto.
CONTACT_ENV_VAR = "METABO_CONTACTO"
_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CoverageThresholds(_Strict):
    completa: float = Field(gt=0, le=100)
    casi_completa: float = Field(gt=0, le=100)
    parcial: float = Field(gt=0, le=100)

    @model_validator(mode="after")
    def _ordered(self) -> CoverageThresholds:
        if not self.completa > self.casi_completa > self.parcial:
            raise ValueError("Los umbrales deben cumplir completa > casi_completa > parcial.")
        return self


class CoverageConfig(_Strict):
    umbrales: CoverageThresholds


class DownloadConfig(_Strict):
    contacto: str | None = Field(default=None, pattern=_EMAIL, description="Correo de contacto.")
    producto: str = Field(min_length=1)
    url_proyecto: str = Field(pattern=r"^https://")
    timeout_segundos: float = Field(gt=0)
    reintentos: int = Field(ge=1, le=10)
    espera_inicial_segundos: float = Field(ge=0)
    espera_maxima_segundos: float = Field(ge=0)


class DirectoriesConfig(_Strict):
    crudos: str = Field(min_length=1)
    staging: str = Field(min_length=1)
    salida: str = Field(min_length=1)


class PipelineConfig(_Strict):
    cobertura: CoverageConfig
    descargas: DownloadConfig
    directorios: DirectoriesConfig


def _apply_contact_from_env(data: Any) -> Any:
    contact = os.environ.get(CONTACT_ENV_VAR, "").strip()
    if not contact or not isinstance(data, dict) or not isinstance(data.get("descargas"), dict):
        return data
    if not re.match(_EMAIL, contact):
        # No se muestra el valor: puede venir de un secreto.
        raise ConfigError(f"La variable de entorno {CONTACT_ENV_VAR} no es un correo válido.")
    data["descargas"]["contacto"] = contact
    return data


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> PipelineConfig:
    """Lee config.yaml. El correo de contacto se toma de METABO_CONTACTO si está definida."""
    try:
        return PipelineConfig.model_validate(_apply_contact_from_env(load_yaml(path)))
    except ValidationError as exc:
        raise ConfigError(f"{path} no es válido:\n{exc}") from exc

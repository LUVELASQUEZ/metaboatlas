"""Configuración del pipeline (pipeline/config.yaml)."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from metabo.errors import ConfigError
from metabo.paths import PIPELINE_DIR
from metabo.yamlio import load_yaml

DEFAULT_CONFIG_PATH = PIPELINE_DIR / "config.yaml"


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
    contacto: str | None = Field(
        default=None, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", description="Correo de contacto."
    )
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


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> PipelineConfig:
    try:
        return PipelineConfig.model_validate(load_yaml(path))
    except ValidationError as exc:
        raise ConfigError(f"{path} no es válido:\n{exc}") from exc

"""Fixtures compartidas. Todas las fuentes y URLs de prueba son ficticias (.invalid)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from metabo.config import DownloadConfig
from metabo.registry import SourceRegistry

FAKE_SOURCES = {
    "fuente_prueba": {
        "nombre": "Fuente de prueba (ficticia)",
        "uso": "redistribuir",
        "estado": "verificada",
        "url": "https://datos.ejemplo.invalid",
        "licencia": "CC BY 4.0",
        "licencia_url": "https://datos.ejemplo.invalid/licencia",
        "verificada": "2026-10-01",
        "que_tomamos": "Datos ficticios para pruebas.",
        "condicion": "Atribución.",
        "acceso": ["datos.ejemplo.invalid/descargas/"],
        "plantillas": {"registro": "https://datos.ejemplo.invalid/registro/{id}"},
        "cita_recomendada": "Cita ficticia para pruebas.",
        "doi_cita": None,
        "notas": None,
    },
    "fuente_pendiente": {
        "nombre": "Fuente pendiente (ficticia)",
        "uso": "redistribuir",
        "estado": "pendiente de verificar",
        "url": None,
        "licencia": "CC BY 4.0",
        "licencia_url": None,
        "verificada": None,
        "que_tomamos": "Datos ficticios.",
        "condicion": None,
        "acceso": ["pendiente.ejemplo.invalid/"],
        "plantillas": {},
        "cita_recomendada": None,
        "doi_cita": None,
        "notas": None,
    },
    "fuente_enlace": {
        "nombre": "Fuente de solo enlace (ficticia)",
        "uso": "solo_enlace",
        "estado": "verificada",
        "url": None,
        "licencia": "Uso restringido",
        "licencia_url": "https://enlace.ejemplo.invalid/terminos",
        "verificada": "2026-10-01",
        "que_tomamos": "nada",
        "condicion": "Solo enlace.",
        "acceso": [],
        "plantillas": {"entrada": "https://enlace.ejemplo.invalid/entry/{id}"},
        "cita_recomendada": None,
        "doi_cita": None,
        "notas": None,
    },
}


@pytest.fixture
def sources_path(tmp_path: Path) -> Path:
    path = tmp_path / "sources.yaml"
    path.write_text(yaml.safe_dump(FAKE_SOURCES, allow_unicode=True), encoding="utf-8")
    return path


@pytest.fixture
def registry(sources_path: Path) -> SourceRegistry:
    return SourceRegistry.load(sources_path)


@pytest.fixture
def download_config() -> DownloadConfig:
    return DownloadConfig(
        contacto="pruebas@ejemplo.invalid",
        producto="MetaboAtlas",
        url_proyecto="https://github.com/LUVELASQUEZ/metaboatlas",
        timeout_segundos=5,
        reintentos=3,
        espera_inicial_segundos=1,
        espera_maxima_segundos=4,
    )

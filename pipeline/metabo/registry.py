"""Registro de fuentes (sources.yaml): qué se puede descargar y cómo se enlaza.

Reglas 1 y 2 de CLAUDE.md: solo se descargan fuentes registradas, de uso
`redistribuir` y con la licencia verificada; las fuentes `solo_enlace` nunca se
descargan, solo se enlazan.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Literal
from urllib.parse import quote, urlsplit

from pydantic import BaseModel, ConfigDict

from metabo import schemas
from metabo.errors import ConfigError, SourceNotAllowedError
from metabo.paths import repo_root
from metabo.yamlio import load_yaml


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str
    nombre: str
    uso: Literal["redistribuir", "por_verificar", "solo_enlace"]
    estado: Literal["pendiente de verificar", "verificada"]
    url: str | None
    licencia: str | None
    licencia_url: str | None
    verificada: str | None
    que_tomamos: str | None
    condicion: str | None
    acceso: tuple[str, ...]
    plantillas: Mapping[str, str]
    cita_recomendada: str | None
    doi_cita: str | None
    notas: str | None
    # La base no publica una cita recomendada (la regla 6 impide escribir una).
    sin_cita_oficial: bool = False

    @property
    def downloadable(self) -> bool:
        return self.uso == "redistribuir" and self.estado == "verificada"


def _matches_access_prefix(url: str, prefix: str) -> bool:
    """True si `url` (https) está bajo el prefijo de acceso `prefix` (sin esquema)."""
    parts = urlsplit(url)
    target = f"{parts.netloc}{parts.path}"
    prefix = prefix.removeprefix("https://")
    if not target.startswith(prefix):
        return False
    # Evita que "dominio.org" acepte "dominio.org.otro.com" o "dominio.organizacion".
    rest = target[len(prefix) :]
    return prefix.endswith("/") or rest == "" or rest.startswith("/")


class SourceRegistry:
    def __init__(self, sources: Mapping[str, Source]):
        self._sources = dict(sources)

    @classmethod
    def load(cls, path: Path | None = None) -> SourceRegistry:
        path = path or repo_root() / "sources.yaml"
        data = load_yaml(path)
        schemas.validate("fuentes", data, label=str(path))
        return cls({key: Source(key=key, **entry) for key, entry in data.items()})

    def __iter__(self):
        return iter(self._sources.values())

    def get(self, key: str) -> Source:
        try:
            return self._sources[key]
        except KeyError:
            raise SourceNotAllowedError(
                f"La fuente '{key}' no está registrada en sources.yaml; no se puede usar."
            ) from None

    def require_downloadable(self, key: str) -> Source:
        """Devuelve la fuente si se puede descargar; si no, explica por qué."""
        source = self.get(key)
        if source.uso == "solo_enlace":
            raise SourceNotAllowedError(
                f"{source.nombre} es una fuente de solo enlace: nunca se descargan sus datos."
            )
        if source.uso == "por_verificar":
            raise SourceNotAllowedError(
                f"La licencia de {source.nombre} está por verificar: no se puede integrar todavía."
            )
        if source.estado != "verificada":
            raise SourceNotAllowedError(
                f"{source.nombre} está '{source.estado}' en sources.yaml: verifica su licencia "
                "y su cita antes de descargar."
            )
        return source

    def require_official_url(self, source: Source, url: str) -> None:
        """Exige https y que la URL esté bajo uno de los accesos oficiales registrados."""
        if urlsplit(url).scheme != "https":
            raise SourceNotAllowedError(f"Solo se descarga por https: {url}")
        if not any(_matches_access_prefix(url, prefix) for prefix in source.acceso):
            raise SourceNotAllowedError(
                f"{url} no está entre los accesos oficiales de {source.nombre} en sources.yaml."
            )

    def build_link(self, fuente: str, tipo: str, id: str) -> str:
        """Construye el enlace de una referencia cruzada {fuente, tipo, id}."""
        source = self.get(fuente)
        try:
            template = source.plantillas[tipo]
        except KeyError:
            raise ConfigError(
                f"La fuente '{fuente}' no tiene la plantilla de enlace '{tipo}' en sources.yaml."
            ) from None
        return template.replace("{id}", quote(id, safe=":"))

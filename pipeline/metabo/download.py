"""Descargas oficiales con User-Agent de contacto, reintentos y checksum SHA-256.

Regla 3 de CLAUDE.md: nada de scraping. Solo se descargan URLs bajo los accesos
oficiales registrados en sources.yaml, de fuentes verificadas, con reintentos
y espera exponencial.
"""

from __future__ import annotations

import hashlib
import re
import time
from collections.abc import Callable
from datetime import date
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

import httpx
from tenacity import (
    RetryError,
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from metabo import __version__
from metabo.config import CONTACT_ENV_VAR, DownloadConfig
from metabo.errors import ConfigError, DownloadError
from metabo.manifest import DownloadRecord
from metabo.registry import Source, SourceRegistry

_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_CHUNK_SIZE = 1 << 16


def _is_retryable(exc: BaseException) -> bool:
    """Errores de red, 429 y 5xx se reintentan; los demás 4xx no."""
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        return status == 429 or status >= 500
    return isinstance(exc, httpx.TransportError)


def _safe_segment(value: str, what: str) -> str:
    if not _SAFE_SEGMENT.match(value):
        raise DownloadError(f"{what} no válido para una ruta de archivo: {value!r}")
    return value


class Downloader:
    def __init__(
        self,
        config: DownloadConfig,
        registry: SourceRegistry,
        raw_dir: Path,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        if not config.contacto:
            raise ConfigError(
                f"Falta el correo de contacto: define la variable de entorno {CONTACT_ENV_VAR}. "
                "Las fuentes piden un correo en el User-Agent; no se descarga nada sin él."
            )
        self._config = config
        self._registry = registry
        self._raw_dir = raw_dir
        self._sleep = sleep
        self._client = client or httpx.Client(
            timeout=config.timeout_segundos, follow_redirects=True
        )
        self._client.headers["User-Agent"] = self.user_agent

    @property
    def user_agent(self) -> str:
        c = self._config
        return f"{c.producto}/{__version__} (+{c.url_proyecto}; mailto:{c.contacto})"

    def download(
        self,
        fuente: str,
        url: str,
        version: str,
        filename: str | None = None,
        today: date | None = None,
    ) -> DownloadRecord:
        """Descarga `url` a raw/<fuente>/<version>/<archivo> y devuelve su registro."""
        source = self._registry.require_downloadable(fuente)
        self._registry.require_official_url(source, url)
        version = _safe_segment(version, "Versión")
        filename = _safe_segment(filename or PurePosixPath(urlsplit(url).path).name, "Archivo")

        relative = PurePosixPath(fuente, version, filename)
        target = self._raw_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_name(target.name + ".parcial")

        retrying = Retrying(
            stop=stop_after_attempt(self._config.reintentos),
            wait=wait_exponential(
                multiplier=self._config.espera_inicial_segundos,
                max=self._config.espera_maxima_segundos,
            ),
            retry=retry_if_exception(_is_retryable),
            sleep=self._sleep,
            reraise=False,
        )
        try:
            digest, size = retrying(self._fetch, source, url, partial)
        except RetryError as exc:
            partial.unlink(missing_ok=True)
            cause = exc.last_attempt.exception()
            raise DownloadError(
                f"No se pudo descargar {url} tras {self._config.reintentos} intentos: {cause}"
            ) from cause
        except httpx.HTTPError as exc:
            partial.unlink(missing_ok=True)
            raise DownloadError(f"No se pudo descargar {url}: {exc}") from exc
        except BaseException:
            partial.unlink(missing_ok=True)
            raise
        partial.replace(target)

        return DownloadRecord(
            fuente=fuente,
            url=url,
            version=version,
            fecha_descarga=(today or date.today()).isoformat(),
            archivo=relative.as_posix(),
            sha256=digest,
            bytes=size,
            licencia=source.licencia or "",
        )

    def _fetch(self, source: Source, url: str, destination: Path) -> tuple[str, int]:
        sha = hashlib.sha256()
        size = 0
        with self._client.stream("GET", url) as response:
            # Una redirección no puede sacar la descarga de los accesos oficiales.
            self._registry.require_official_url(source, str(response.url))
            response.raise_for_status()
            with destination.open("wb") as handle:
                for chunk in response.iter_bytes(_CHUNK_SIZE):
                    sha.update(chunk)
                    size += len(chunk)
                    handle.write(chunk)
        return sha.hexdigest(), size

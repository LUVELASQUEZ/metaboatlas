"""Manifiesto de procedencia (manifest.json): una entrada por descarga con su SHA-256."""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from metabo import schemas
from metabo.errors import ConfigError


class DownloadRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fuente: str
    url: str
    version: str
    fecha_descarga: str
    archivo: str
    sha256: str
    bytes: int
    licencia: str


class Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version_datos: str
    generado: str = Field(default="")
    descargas: list[DownloadRecord] = Field(default_factory=list)

    def add(self, record: DownloadRecord) -> None:
        """Agrega una descarga; si el archivo ya estaba registrado, la reemplaza."""
        self.descargas = [d for d in self.descargas if d.archivo != record.archivo]
        self.descargas.append(record)

    def write(self, path: Path) -> None:
        """Escribe el manifiesto después de validarlo contra schema/manifiesto.schema.json."""
        self.generado = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        data = self.model_dump()
        data["descargas"].sort(key=lambda d: d["archivo"])
        schemas.validate("manifiesto", data, label="manifest.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def latest(self, fuente: str, required: Sequence[str] = ()) -> tuple[str, dict[str, str]]:
        """Versión más reciente descargada de `fuente` y sus archivos (nombre -> ruta en raw/).

        Lanza ConfigError si no hay descargas de la fuente o si falta algún archivo de
        `required` en esa versión.
        """
        records = [d for d in self.descargas if d.fuente == fuente]
        if not records:
            raise ConfigError(
                f"No hay descargas de {fuente} en raw/manifest.json: "
                f"ejecuta `uv run metabo extraer {fuente}`."
            )
        latest = max(records, key=lambda d: (d.fecha_descarga, d.version))
        files = {Path(d.archivo).name: d.archivo for d in records if d.version == latest.version}
        missing = [name for name in required if name not in files]
        if missing:
            raise ConfigError(
                f"La versión {latest.version} de {fuente} no tiene {', '.join(missing)}: "
                f"vuelve a ejecutar `uv run metabo extraer {fuente}`."
            )
        return latest.version, files

    @classmethod
    def read(cls, path: Path) -> Manifest:
        data = json.loads(path.read_text(encoding="utf-8"))
        schemas.validate("manifiesto", data, label=str(path))
        return cls.model_validate(data)

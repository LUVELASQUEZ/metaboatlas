"""ATRIBUCION.md del paquete de datos: de dónde sale cada dato y cómo citarlo.

Acompaña al paquete en el release `data-<version>` para que toda copia lleve la
atribución que piden las licencias (regla 4 de CLAUDE.md). Los textos de licencia,
condición y cita se copian de sources.yaml, nunca se escriben de memoria.
"""

from __future__ import annotations

from metabo.manifest import Manifest
from metabo.registry import SourceRegistry


def attribution(manifest: Manifest, registry: SourceRegistry) -> str:
    """Texto en Markdown con las fuentes del paquete, sus versiones, licencias y citas."""
    lines = [
        f"# Paquete de datos de MetaboAtlas {manifest.version_datos}",
        "",
        "Datos compilados por MetaboAtlas a partir de bases de licencia abierta. La "
        "compilación se distribuye bajo CC BY 4.0 (LICENSE-content del repositorio); cada "
        "fuente conserva su propia licencia y su atribución, que se detallan abajo.",
        "",
        "Que un paso no tenga anotación en un organismo no significa que el organismo "
        "carezca de la enzima: solo que no se encontró evidencia en estas bases.",
    ]
    versions: dict[str, dict[str, str]] = {}
    for d in manifest.descargas:
        versions.setdefault(d.fuente, {})[d.version] = d.fecha_descarga
    for key in sorted(versions):
        source = registry.get(key)
        lines += ["", f"## {source.nombre}", ""]
        if source.url:
            lines.append(f"- Sitio: {source.url}")
        for version, fecha in sorted(versions[key].items()):
            lines.append(f"- Versión {version}, descargada el {fecha}.")
        licencia = source.licencia or "sin licencia registrada"
        if source.licencia_url:
            licencia += f" ({source.licencia_url})"
        lines.append(f"- Licencia: {licencia}")
        if source.condicion:
            lines.append(f"- Condición de uso: {' '.join(source.condicion.split())}")
        if source.cita_recomendada:
            lines += ["", "Cita recomendada:", ""]
            lines += [f"> {line}" for line in source.cita_recomendada.splitlines()]
            if source.doi_cita:
                lines += [">", f"> https://doi.org/{source.doi_cita}"]
    return "\n".join(lines) + "\n"

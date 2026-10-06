# pipeline/

Pipeline de datos en Python 3.12 (gestor `uv`). Descarga las fuentes registradas en `../sources.yaml`, las normaliza en DuckDB, integra la curaduría, calcula la cobertura, valida contra `../schema/` y exporta el paquete de datos.

Comando principal (pendiente): `uv run metabo build`.

Ver la sección 6 de `docs/MANUAL.md`.

Archivos previstos:

- `config.yaml`: umbrales de cobertura y parámetros (pendiente).
- `organismos.yaml`: lista curada de organismos (pendiente; el código no asume un número fijo).

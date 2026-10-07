# pipeline/metabo/sources/

Un módulo de extracción por base de datos (`rhea.py`, `uniprot.py`, …). Solo descargas oficiales y API documentadas de fuentes registradas en `sources.yaml`; User-Agent con correo de contacto, reintentos con espera exponencial y registro SHA-256 en `manifest.json`.

Cada extractor expone `extract(downloader, raw_dir)`: descarga a `raw/<fuente>/<versión>/` con el descargador común, comprueba el formato de cada archivo (si la fuente cambia sus columnas, se detiene con `SourceFormatError`) y devuelve los registros para `raw/manifest.json`. Se ejecuta con `uv run metabo extraer <fuente>`.

| Fuente | Módulo | Archivos | Versión |
| --- | --- | --- | --- |
| Rhea | `rhea.py` | `rhea-release.properties`, `tsv/rhea-directions.tsv`, `tsv/rhea2ec.tsv` | `rhea.release.number` de `rhea-release.properties` |

Pendiente en Rhea: los participantes ChEBI de cada reacción no están en los TSV del FTP (solo en el volcado RDF y en SPARQL). TODO: elegir cómo obtenerlos al implementar ChEBI.

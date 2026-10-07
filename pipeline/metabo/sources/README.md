# pipeline/metabo/sources/

Un módulo de extracción por base de datos (`rhea.py`, `uniprot.py`, …). Solo descargas oficiales y API documentadas de fuentes registradas en `sources.yaml`; User-Agent con correo de contacto, reintentos con espera exponencial y registro SHA-256 en `manifest.json`.

Cada extractor expone `extract(downloader, raw_dir)`: descarga a `raw/<fuente>/<versión>/` con el descargador común, comprueba el formato de cada archivo (si la fuente cambia sus columnas, se detiene con `SourceFormatError`) y devuelve los registros para `raw/manifest.json`. Se ejecuta con `uv run metabo extraer <fuente>`.

| Fuente | Módulo | Archivos | Versión |
| --- | --- | --- | --- |
| Rhea | `rhea.py` | `rhea-release.properties`, `tsv/rhea-directions.tsv`, `tsv/rhea2ec.tsv` | `rhea.release.number` de `rhea-release.properties` |
| ENZYME | `enzyme.py` | `enzclass.txt`, `enzyme.dat` | Fecha "Release" de ambos archivos, en ISO (deben coincidir) |
| ChEBI | `chebi.py` | `flat_files/README` y `flat_files/{compounds,chemical_data,names,relation,relation_type,secondary_ids}.tsv.gz` | "ChEBI Release" del README de `flat_files/` |

Las comprobaciones compartidas (encabezados de TSV, también comprimidos, y fechas de versión) están en `formats.py`.

Pendientes:

- Rhea: los participantes ChEBI de cada reacción no están en los TSV del FTP (solo en el volcado RDF y en SPARQL). TODO: elegir cómo obtenerlos.
- ChEBI: `structures.tsv.gz` (SMILES e InChI, ~89 MB) y `reference.tsv.gz` (~131 MB) todavía no se descargan. TODO: agregarlos cuando una etapa los use.
- ChEBI: el README de `flat_files/` contradice su archivo `LICENSE` (ver `notas` de ChEBI en `sources.yaml`).

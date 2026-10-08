# pipeline/metabo/sources/

Un módulo de extracción por base de datos (`rhea.py`, `uniprot.py`, …). Solo descargas oficiales y API documentadas de fuentes registradas en `sources.yaml`; User-Agent con correo de contacto, reintentos con espera exponencial y registro SHA-256 en `manifest.json`.

Cada extractor expone `extract(downloader, raw_dir)`: descarga a `raw/<fuente>/<versión>/` con el descargador común, comprueba el formato de cada archivo (si la fuente cambia sus columnas, se detiene con `SourceFormatError`) y devuelve los registros para `raw/manifest.json`. Se ejecuta con `uv run metabo extraer <fuente>`.

| Fuente | Módulo | Archivos | Versión |
| --- | --- | --- | --- |
| Rhea | `rhea.py` | `rhea-release.properties`, `tsv/rhea-directions.tsv`, `tsv/rhea2ec.tsv`, `txt/rhea-reactions.txt.gz` (ecuación con participantes ChEBI) | `rhea.release.number` de `rhea-release.properties` |
| ENZYME | `enzyme.py` | `enzclass.txt`, `enzyme.dat` | Fecha "Release" de ambos archivos, en ISO (deben coincidir) |
| UniProtKB | `uniprot.py` | Por cada organismo de `organismos.yaml`: `<UP>.json` (ficha del proteoma de referencia, `rest.uniprot.org/proteomes/<UP>`) y `<UP>.tsv.gz` (todas sus proteínas, revisadas y no revisadas, con los campos de `uniprot.FIELDS`, de `rest.uniprot.org/uniprotkb/stream?query=proteome:<UP>`) | Cabecera `X-UniProt-Release` de la API (p. ej. `2026_03`); todas las respuestas deben traer la misma |
| Wikidata | `wikidata.py` | `compuestos-NNN.json` y `enzimas-NNN.json`: respuestas SPARQL JSON de `query.wikidata.org/sparql` con el elemento y la etiqueta en español de cada ChEBI (P683) y EC (P591) del paquete, en lotes de 200 | Fecha de la consulta (Wikidata no tiene versiones) |
| Europe PMC | `europe_pmc.py` | `referencias-NNN.json`: respuestas de la API REST (`www.ebi.ac.uk/europepmc/webservices/rest/search`, `resultType=lite`, sin resúmenes) con los datos de cita de los PMID de `curation/referencias.yaml`, en lotes de 50 | Fecha de la consulta (Europe PMC no tiene versiones) |
| ChEBI | `chebi.py` | `flat_files/README` y `flat_files/{compounds,chemical_data,names,relation,relation_type,secondary_ids}.tsv.gz` | "ChEBI Release" del README de `flat_files/` |

Los módulos también leen lo descargado para la curaduría (`rhea.read_reactions`, `enzyme.read_entries`, `chebi.read_compound_names`).

UniProt también se detiene si un proteoma deja de ser de referencia o si el TSV no tiene tantas filas como el `proteinCount` del proteoma (el stream de la API puede cortarse sin error).

Las comprobaciones compartidas (encabezados de TSV, también comprimidos, y fechas de versión) están en `formats.py`.

Wikidata no se descarga entera: `metabo extraer wikidata` consulta solo los compuestos y EC de las vías curadas (participantes de sus reacciones en Rhea, nodos de sus mapas y EC de sus pasos), así que Rhea debe extraerse antes. `wikidata.read_labels` solo devuelve una etiqueta si el ID tiene una sola etiqueta en español distinta: Wikidata pone EC 2.7.1.1 en "hexocinasa" y en "glucocinasa", y ese caso queda sin nombre.

Europe PMC solo aporta datos de cita (decisión del 2026-10-08): el extractor se detiene si una respuesta trae resúmenes o si falta algún PMID pedido.

Pendientes:

- Wikidata: los taxones (P685) no se consultan. Sus etiquetas en español son el nombre de la cepa o faltan (*Homo sapiens* no tiene), así que el nombre común en español sale de `curation/nombres_es.yaml`. Tampoco se toman los enlaces a Wikipedia en español.

- ChEBI: `structures.tsv.gz` (SMILES e InChI, ~89 MB) y `reference.tsv.gz` (~131 MB) todavía no se descargan. TODO: agregarlos cuando una etapa los use.
- ChEBI: el README de `flat_files/` contradice su archivo `LICENSE` (ver `notas` de ChEBI en `sources.yaml`).

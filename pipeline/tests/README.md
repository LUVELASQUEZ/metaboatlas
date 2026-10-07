# pipeline/tests/

Pruebas con `pytest`, incluidas las verdades biológicas de la sección 14 del manual.

- `test_coverage.py` corre los casos compartidos de [`schema/casos/cobertura.json`](../../schema/casos/cobertura.json), los mismos que pasará la versión TypeScript del algoritmo.
- `test_verdades.py` calcula la cobertura con los datos reales de `raw/`. Necesita `uv run metabo extraer rhea` y `uv run metabo extraer uniprot`; sin esas descargas se omite (por eso no corre en las verificaciones de cada pull request). Si una verdad falla, se investiga: nunca se cambia el resultado esperado para que pase.
- `test_taxonomia_datos.py` comprueba los taxones de `organismos.yaml` contra el volcado real de NCBI Taxonomy (`uv run metabo extraer ncbi_taxonomy`); sin esa descarga se omite.

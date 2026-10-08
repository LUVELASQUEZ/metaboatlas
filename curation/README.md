# curation/

Curaduría manual: la única parte del proyecto que no sale de una base de datos.

- `vias/*.yaml`: definición de cada vía (módulos, pasos, Rhea, EC). Se verifica con `uv run metabo curar validar`.
- `compuestos.yaml`: reglas para la clase de cada compuesto (derivada de la ontología de ChEBI) y lista de cofactores y metabolitos "moneda". `uv run metabo exportar` comprueba que cada ID tenga en ChEBI el nombre que dice el archivo.
- `mapas/*.json`: coordenadas del dibujo de cada vía.
- `nombres_es.yaml`: nombres en español de compuestos, enzimas y organismos, con los criterios de traducción. Tienen prioridad sobre las etiquetas de Wikidata. `uv run metabo exportar` comprueba que el nombre `en` de cada entrada coincida con ChEBI, ENZYME o NCBI Taxonomy.

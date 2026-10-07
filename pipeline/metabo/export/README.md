# pipeline/metabo/export/

Exportación del paquete de datos (secciones 4 y 6 de `docs/MANUAL.md`): `uv run metabo exportar` escribe `data/<version_datos>/` y valida cada archivo contra `schema/`.

```
data/2026.10/
  manifest.json                 # descargas usadas: fuente, versión, fecha, licencia, SHA-256
  vias/glucolisis.json          # la curaduría de curation/vias/
  reacciones/RHEA_14729.json    # reacciones de los pasos (Rhea)
  compuestos/CHEBI_15361.json   # participantes de esas reacciones (ChEBI)
  enzimas/EC_2.7.1.1.json       # EC de los pasos (ENZYME, Rhea) y sus proteínas por organismo (UniProt)
  organismos/511145.json        # organismos.yaml + NCBI Taxonomy + UniProt
  cobertura/glucolisis/511145.json
  mapas/glucolisis.json         # el dibujo de curation/mapas/, verificado contra Rhea
```

- `package.py` arma los documentos. Solo exporta las entidades que tocan las vías curadas, y cada una lleva su `procedencia` (fuente, ID, versión y fecha de descarga). Una exportación nueva reemplaza la carpeta de la misma versión.
- Los mapas de `curation/mapas/` se verifican con `metabo/maps.py` (ver [`curation/mapas/README.md`](../../../curation/mapas/README.md)) y sus nodos también se exportan como compuestos.
- `compounds.py` decide la clase de cada compuesto y si es cofactor, con las reglas de [`curation/compuestos.yaml`](../../../curation/compuestos.yaml).

## De dónde sale cada campo

| Campo | Fuente |
| --- | --- |
| Ecuación, participantes, direcciones, EC de una reacción | Rhea (`rhea-reactions.txt.gz`, `rhea-directions.tsv`, `rhea2ec.tsv`) |
| `es_transporte` | Rhea: la ecuación marca compartimentos, p. ej. `sulfate(out) … = sulfate(in) …` |
| Nombre, definición, sinónimos, fórmula, carga y masa monoisotópica | ChEBI (`compounds`, `names`, `chemical_data`); las etiquetas HTML de los nombres se quitan |
| Clase y `es_cofactor` | Ontología de ChEBI ("is a" y ácido/base conjugados) + `curation/compuestos.yaml` |
| Nombre, nombres alternativos y reacción de una enzima | ENZYME (`enzyme.dat`, líneas DE, AN y CA) |
| Proteínas de una enzima | UniProt: proteínas de cada proteoma con ese EC exacto |
| Rango, linaje, dominio y nombre común de un organismo | NCBI Taxonomy |
| `codigo_kegg` | Prefijo más frecuente en las referencias KEGG de UniProt (KEGG: solo enlace) |

## Pendiente (vacío o `null`, nunca inventado)

- SMILES, InChI e InChIKey: falta descargar `structures.tsv.gz` de ChEBI.
- Nombres en español (`nombre.es`): vendrán de Wikidata.
- Referencias cruzadas de compuestos y reacciones (KEGG, HMDB, PubChem…): falta `reference.tsv.gz` de ChEBI.
- Reversibilidad y ΔG de las reacciones, tinción de Gram y cepa: no hay fuente verificada todavía. `gram` es `no_aplica` en organismos que no son bacterias.
- Cofactores de las enzimas: el `enzyme.dat` vigente no trae líneas CF; el lector las entiende si vuelven.
- Índices de búsqueda y changelog de datos.

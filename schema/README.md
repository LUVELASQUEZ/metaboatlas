# schema/

Contrato único entre el pipeline y la web (sección 12 de `docs/MANUAL.md`). El pipeline valida su salida contra estos esquemas y la web genera sus tipos (Zod/TypeScript) a partir de ellos. Si un campo cambia, ambos lados deben fallar en las pruebas antes de llegar a producción.

Todos los esquemas usan JSON Schema **draft 2020-12**.

| Esquema | Describe | Archivo del paquete de datos |
| --- | --- | --- |
| `comun.schema.json` | Tipos compartidos: CURIE, slugs, textos bilingües, `xref`, `procedencia`, proteína y estados de evidencia | — |
| `via.schema.json` | Vía de referencia con sus módulos y pasos | `vias/<slug>.json` |
| `paso.schema.json` | Paso de una vía (se usa dentro de `via`) | — |
| `compuesto.schema.json` | Compuesto (ChEBI) | `compuestos/CHEBI_<n>.json` |
| `reaccion.schema.json` | Reacción (Rhea, ID maestro) | `reacciones/RHEA_<n>.json` |
| `enzima.schema.json` | Actividad enzimática (EC) y proteínas por organismo | `enzimas/EC_<n>.json` |
| `organismo.schema.json` | Organismo (NCBI Taxonomy + UniProt) | `organismos/<taxon>.json` |
| `cobertura.schema.json` | Cobertura de una vía en un organismo | `cobertura/<slug>/<taxon>.json` |
| `mapa.schema.json` | Dibujo curado de una vía: posiciones de compuestos, flechas por paso y módulos | `mapas/<slug>.json` |
| `fuentes.schema.json` | Estructura de `sources.yaml` | `sources.yaml` |
| `manifiesto.schema.json` | Procedencia: cada descarga con URL, versión, fecha, licencia y SHA-256 | `manifest.json` |

## Decisiones de diseño

- **Claves en español**, como en el manual (`nombre`, `pasos`, `cobertura`).
- **IDs externos en formato CURIE** con patrón validado (`CHEBI:`, `RHEA:`, `EC:`, `UNIPROT:`, `taxon:`).
- **Trazabilidad:** toda entidad que sale de una fuente externa exige `procedencia` (fuente, ID, versión y fecha de descarga). La vía y la cobertura registran la versión de cada fuente en `fuentes`.
- **Referencias cruzadas como pares** `{fuente, tipo, id}`, los tres obligatorios. `fuente` es una clave de `sources.yaml`, `tipo` es la clave de una de sus plantillas de URL e `id` es el ID nativo que reemplaza `{id}` en la plantilla. Esto reemplaza el objeto `xrefs` del ejemplo de la sección 4 del manual (`{"kegg_map": …}`) por tres razones:
  - **Arquitectura:** un solo formato y una sola función construyen todos los enlaces; agregar una base nueva es agregar una entrada en `sources.yaml`, no una clave nueva en cada esquema.
  - **Trazabilidad:** una entidad puede tener varios IDs en la misma fuente (por ejemplo, varias vías de Reactome) y cada par se vincula a la licencia y la cita de su fuente.
  - **Comprensión:** la web puede mostrar el nombre de la base junto a cada ID usando `sources.yaml`.
- **IDs nativos en `xrefs` y `procedencia`:** el campo `id` lleva el ID tal como lo usa la fuente, sin prefijo CURIE (`15361`, `P0A6T1`, `map00010`). El `id` de la entidad sí va en CURIE (`CHEBI:15361`).
- **Nunca "ausente":** los estados de evidencia son `espontaneo`, `alta`, `media`, `baja` y `sin_anotacion`.
- **Coherencia de la cobertura:** un paso `alta`, `media` o `baja` debe citar al menos una proteína; uno `espontaneo` o `sin_anotacion`, ninguna.
- **Pasos enzimáticos:** un paso no espontáneo debe tener al menos una reacción Rhea.
- **Sin dato no es "no aplica":** en `organismo.gram`, `no_aplica` (organismos que no son bacterias) se distingue de `null` (sin dato con fuente).
- **Nombre en español pendiente:** en entidades que vienen de bases de datos, `nombre.es` puede ser `null`. Así queda marcado para traducción manual. En las vías curadas es obligatorio.

## Lo que JSON Schema no valida

Estas reglas quedan para la etapa de validación del pipeline (integridad referencial, sección 14):

- Que los pasos de cada módulo existan en `pasos` de la misma vía y que los IDs de paso no se repitan.
- Que todo ID citado (Rhea, ChEBI, EC, vía, taxón) exista en el paquete de datos.
- Que `xrefs[].fuente` y las claves de `fuentes` existan en `sources.yaml`.
- Que el mapa de una vía dibuje cada paso una vez y que cada flecha corresponda a una reacción Rhea del paso (lo verifica `pipeline/metabo/maps.py`).
- Que `cobertura` y `clase` sean coherentes con los estados de los pasos y con los umbrales de `pipeline/config.yaml`.
- Que una fuente con `estado: pendiente de verificar` no se use para descargar datos.

## Casos del algoritmo de cobertura

[`casos/cobertura.json`](casos/cobertura.json) es la especificación ejecutable del algoritmo de la sección 5 del manual: cada caso da los pasos de una vía, las proteínas de un organismo y el resultado esperado. La implementación Python (`pipeline/metabo/coverage/`) y la TypeScript del modo en vivo (`web/lib/`) deben pasar los mismos casos. Si cambia una regla, se cambia aquí primero.

Sus IDs son centinelas, como los de los ejemplos: Rhea por debajo de 10000 (el ID más bajo de Rhea 142 es 10000), EC de la clase 9 (no existe) y accesiones UniProt `Z9Z99n`, que no aparecen en los proteomas descargados.

## Ejemplos y validación

`ejemplos/validos/<esquema>.json` deben pasar y `ejemplos/invalidos/<esquema>--<motivo>.json` deben fallar.

> **Los ejemplos son ficticios.** Sirven solo para probar el formato y nunca deben copiarse a `curation/` ni al paquete de datos. Sus nombres, fórmulas y ecuaciones dicen "ficticio" o "ejemplo".

Para no asociar datos falsos a registros reales, los ejemplos usan IDs centinela que no existen en la fuente siempre que el formato lo permite. Que un centinela no existe se comprobará contra los datos descargados cuando cada fuente esté verificada. Cuando el formato no admite un valor imposible, usan IDs que el manual o `CLAUDE.md` ya muestran como ejemplo de formato.

| Tipo | ID en los ejemplos | Por qué |
| --- | --- | --- |
| ChEBI | `CHEBI:0` | Centinela: los IDs de ChEBI empiezan en 1. |
| Rhea | `RHEA:0` a `RHEA:3` | Centinela: por debajo del rango de IDs de Rhea. |
| KEGG compuesto | `C00000` | Centinela: los IDs de KEGG COMPOUND empiezan en C00001. |
| EC | `EC:2.7.1.1` | El formato no admite un valor imposible; tomado del manual. |
| UniProt | `UNIPROT:P0A6T1` | Ídem. |
| Taxón | `taxon:511145` | Ídem; tomado de `CLAUDE.md`. |
| KEGG mapa | `map00010` | Ídem; tomado del manual. |

Para validar los esquemas, los ejemplos y `sources.yaml`, ejecuta desde la raíz del repositorio:

```bash
uv run schema/validate_examples.py
```

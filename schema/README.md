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
| `fuentes.schema.json` | Estructura de `sources.yaml` | `sources.yaml` |

## Decisiones de diseño

- **Claves en español**, como en el manual (`nombre`, `pasos`, `cobertura`).
- **IDs externos en formato CURIE** con patrón validado (`CHEBI:`, `RHEA:`, `EC:`, `UNIPROT:`, `taxon:`).
- **Trazabilidad:** toda entidad que sale de una fuente externa exige `procedencia` (fuente, ID, versión y fecha de descarga). La vía y la cobertura registran la versión de cada fuente en `fuentes`.
- **Referencias cruzadas como pares** `{fuente, tipo, id}`. `fuente` es una clave de `sources.yaml` y `tipo` es la clave de su plantilla de URL. Esto reemplaza el objeto `xrefs` del ejemplo de la sección 4 del manual (`{"kegg_map": …}`) para cumplir la regla "toda referencia cruzada se guarda como par (fuente, id)".
- **Nunca "ausente":** los estados de evidencia son `espontaneo`, `alta`, `media`, `baja` y `sin_anotacion`.
- **Coherencia de la cobertura:** un paso `alta`, `media` o `baja` debe citar al menos una proteína; uno `espontaneo` o `sin_anotacion`, ninguna.
- **Pasos enzimáticos:** un paso no espontáneo debe tener al menos una reacción Rhea.
- **Nombre en español pendiente:** en entidades que vienen de bases de datos, `nombre.es` puede ser `null`. Así queda marcado para traducción manual. En las vías curadas es obligatorio.

## Lo que JSON Schema no valida

Estas reglas quedan para la etapa de validación del pipeline (integridad referencial, sección 14):

- Que los pasos de cada módulo existan en `pasos` de la misma vía y que los IDs de paso no se repitan.
- Que todo ID citado (Rhea, ChEBI, EC, vía, taxón) exista en el paquete de datos.
- Que `xrefs[].fuente` y las claves de `fuentes` existan en `sources.yaml`.
- Que `cobertura` y `clase` sean coherentes con los estados de los pasos y con los umbrales de `pipeline/config.yaml`.
- Que una fuente con `estado: pendiente de verificar` no se use para descargar datos.

## Ejemplos y validación

`ejemplos/validos/<esquema>.json` deben pasar y `ejemplos/invalidos/<esquema>--<motivo>.json` deben fallar.

> **Los ejemplos son ficticios.** Usan identificadores con formato válido, tomados del manual, pero sus nombres, fórmulas, ecuaciones y asociaciones no son datos reales. Sirven solo para probar el formato. Nunca deben copiarse a `curation/` ni al paquete de datos.

Para validar los esquemas, los ejemplos y `sources.yaml`, ejecuta desde la raíz del repositorio:

```bash
uv run schema/validate_examples.py
```

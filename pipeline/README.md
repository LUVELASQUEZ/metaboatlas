# pipeline/

Pipeline de datos de MetaboAtlas en Python 3.12 (gestor `uv`). Descarga las fuentes registradas en [`../sources.yaml`](../sources.yaml), las normaliza en DuckDB, integra la curaduría, calcula la cobertura, valida contra [`../schema/`](../schema/) y exporta el paquete de datos. Ver la sección 6 de [`docs/MANUAL.md`](../docs/MANUAL.md).

> **Estado:** las cinco fuentes de la fase 0 (Rhea, ChEBI, UniProtKB, ENZYME y NCBI Taxonomy) están verificadas en `sources.yaml`. Ya existen los extractores de Rhea, ENZYME y ChEBI (`uv run metabo extraer rhea|enzyme|chebi`) y las ayudas de curaduría (`uv run metabo curar buscar|validar`); los de UniProt y NCBI Taxonomy y el resto de las etapas de `build` se implementan en las próximas tareas.

## Uso

```bash
cd pipeline
uv sync                  # instala Python 3.12 y las dependencias
uv run metabo validate   # valida config.yaml, organismos.yaml y sources.yaml
uv run metabo fuentes    # lista las fuentes y si se pueden descargar
uv run metabo extraer rhea   # descarga la versión vigente de una fuente (rhea, enzyme, chebi) a raw/ y actualiza raw/manifest.json
uv run metabo curar buscar 2.7.1.1   # reacciones Rhea maestras de un EC, con su ecuación y sus ChEBI
uv run metabo curar validar          # verifica los IDs de curation/vias/*.yaml contra raw/ (necesita rhea, enzyme y chebi descargados)
uv run metabo build      # recorre las etapas (por ahora, solo las enumera)
uv run pytest            # pruebas
uv run ruff check . && uv run ruff format --check .   # linter
```

## Correo de contacto

Las fuentes piden un correo de contacto en el User-Agent de las descargas automáticas. Como el repositorio es público, el correo **no** se escribe en `config.yaml`: se lee de la variable de entorno `METABO_CONTACTO`.

```bash
export METABO_CONTACTO="correo-del-proyecto@ejemplo.org"   # en tu terminal
```

En GitHub Actions viene del secreto del repositorio `METABO_CONTACTO` (*Settings → Secrets and variables → Actions*). Si la variable no existe, el pipeline se niega a descargar. Si no es un correo válido, falla sin mostrar su valor.

## Estructura

```
pipeline/
├─ config.yaml          # umbrales de cobertura, parámetros de descarga y directorios
├─ organismos.yaml      # lista curada de organismos (el código no asume un número fijo)
├─ pyproject.toml       # dependencias y comando `metabo`
├─ metabo/
│  ├─ cli.py            # comandos build, validate, fuentes, extraer y curar
│  ├─ config.py         # lectura y validación de config.yaml
│  ├─ organisms.py      # lectura y validación de organismos.yaml
│  ├─ registry.py       # sources.yaml: qué se puede descargar y cómo se enlaza
│  ├─ download.py       # descargador común
│  ├─ manifest.py       # manifest.json con SHA-256
│  ├─ schemas.py        # validación contra schema/
│  ├─ curation.py       # búsqueda y verificación de IDs de curation/vias/ contra raw/
│  ├─ sources/          # un extractor por base de datos (rhea.py, enzyme.py, chebi.py; los demás, próximas tareas)
│  ├─ transform/        # normalización e integración de la curaduría
│  ├─ coverage/         # algoritmo de cobertura
│  └─ export/           # exportación del paquete de datos
└─ tests/
```

Las carpetas `sources/`, `transform/`, `coverage/` y `export/` de la sección 12 del manual viven dentro del paquete `metabo/` para que se puedan importar (`metabo.sources.rhea`).

## Garantías del descargador

El descargador (`metabo/download.py`) aplica las reglas 1 a 4 de `CLAUDE.md` antes de hacer cualquier petición:

1. **Solo fuentes verificadas.** Rechaza las fuentes que no están en `sources.yaml`, las de solo enlace (KEGG, BioCyc, HMDB…), las de uso `por_verificar` y las que siguen "pendiente de verificar".
2. **Solo accesos oficiales.** La URL debe ser `https` y estar bajo uno de los prefijos de `acceso` de la fuente. Si una redirección sale de esos accesos, la descarga se cancela.
3. **Buen comportamiento.** Envía un User-Agent con correo de contacto y reintenta con espera exponencial ante errores de red, 429 y 5xx, con un número máximo de intentos. Los demás errores 4xx no se reintentan.
4. **Trazabilidad.** Guarda en `raw/<fuente>/<version>/<archivo>` y devuelve un registro con URL, versión, fecha, licencia, tamaño y SHA-256 para `manifest.json`, que se valida contra `schema/manifiesto.schema.json`.

## Listo para la primera descarga

- **Correo de contacto:** se lee del secreto `METABO_CONTACTO`.
- **Fuentes:** Rhea, ChEBI, UniProt, ENZYME y NCBI Taxonomy están verificadas en `sources.yaml`.
- **Proteomas:** cada organismo de `organismos.yaml` tiene su `proteoma_referencia`. Las proteínas se descargan por proteoma (`proteome:UP…`), no por taxón, porque UniProt puede registrar el proteoma bajo otro taxón (es el caso de *E. coli* MG1655, cuyo proteoma está bajo el taxón 83333).
- **Taxones:** cada `id` de `organismos.yaml` existe en NCBI Taxonomy (ni fusionado ni eliminado) y su `nombre_ncbi` se copió de `names.dmp`.

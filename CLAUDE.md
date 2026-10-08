# MetaboAtlas — Instrucciones para Claude Code

Aplicación web pública, gratuita y de código abierto para consultar mapas metabólicos. Está dirigida a estudiantes de microbiología, bacteriología, biología, bioquímica, biotecnología y nutrición. Replica la lógica de conexiones de KEGG (vía de referencia + organismos), pero se construye solo con datos de licencia abierta y presenta la información de forma didáctica, en español.

El diseño completo está en `docs/MANUAL.md`. Léelo antes de cualquier tarea que toque datos, arquitectura, diseño o contenido. Si algo de este archivo contradice el manual, este archivo manda; si una tarea contradice ambos, detente y pregunta.

## Reglas que nunca se rompen

1. **Solo datos abiertos.** Únicamente se descargan y redistribuyen datos de fuentes registradas en `sources.yaml` con licencia verificada (CC0, CC BY 4.0, dominio público). Si una fuente no está en `sources.yaml`, no se usa.
2. **KEGG, BioCyc/MetaCyc, HMDB, SMPDB y VMH son solo enlaces.** Nunca llames a sus API, nunca descargues sus archivos, nunca copies ni redibujes sus mapas. Solo se construyen URLs hacia sus páginas.
3. **Nada de scraping.** Solo descargas oficiales y API documentadas, respetando límites de uso, con User-Agent que incluya un correo de contacto y reintentos con espera exponencial.
4. **Trazabilidad total.** Todo dato exportado lleva fuente, ID, versión de la base y fecha de descarga. El manifiesto `manifest.json` registra cada descarga con su checksum SHA-256.
5. **Nunca inventes identificadores** (Rhea, ChEBI, EC, UniProt, taxones, Reactome). Si no puedes obtenerlos de los datos descargados, deja el campo pendiente con un `TODO` y avísalo.
6. **Nunca escribas citas bibliográficas de memoria.** Las citas recomendadas de cada base se copian de su página oficial "How to cite" y se guardan en `sources.yaml`.
7. **"Sin anotación" no es "ausente".** La interfaz nunca afirma que un organismo carece de una vía; dice que no se encontró evidencia.
8. **Costo cero.** Nada de servicios pagos, servidores propios ni bases de datos en producción. El sitio es estático.

## Arquitectura (resumen)

- `pipeline/` — Python 3.12 con `uv`, `httpx` + `tenacity`, `duckdb`, `polars`, `pydantic`, `pytest`. Comando principal: `uv run metabo build`. Etapas: extraer → cargar en DuckDB → normalizar → integrar curaduría → enriquecer → calcular cobertura → validar → exportar → publicar.
- `curation/vias/*.yaml` — definición manual de cada vía (módulos, pasos, Rhea, EC). `curation/mapas/*.json` — coordenadas del dibujo.
- `content/` — MDX en español (vías por niveles, glosario, rutas, preguntas).
- `schema/` — JSON Schema: contrato único entre pipeline y web. El pipeline valida contra él; la web genera sus tipos (Zod/TypeScript) desde él.
- `web/` — Next.js (App Router) con exportación estática, TypeScript, Tailwind, Radix UI, Cytoscape.js, MiniSearch, citation-js.
- `.github/workflows/` — `checks.yml` (PR), `pipeline.yml` (mensual/manual), `web.yml` (despliegue).

## Hosting: GitHub Pages

- El sitio se publica en `https://<usuario>.github.io/metaboatlas/`.
- En `next.config`: `output: 'export'`, `basePath` y `assetPrefix` con `/metaboatlas` (configurable por variable de entorno), `images.unoptimized: true`, `trailingSlash: true`.
- Agrega `.nojekyll` en la carpeta de salida.
- Despliegue con las acciones oficiales de GitHub Pages desde `web.yml`.
- Toda ruta interna y todo `fetch` de JSON debe respetar el `basePath`.

## Convenciones

- **Idioma**: interfaz, contenido, mensajes de commit y documentación en español. Identificadores de código (funciones, variables, archivos de código) en inglés. Las claves de los JSON de datos siguen el manual (en español: `nombre`, `pasos`, `cobertura`).
- **IDs externos** en formato CURIE: `CHEBI:15361`, `RHEA:12345`, `EC:2.7.1.1`, `UNIPROT:P0A6T1`, `taxon:511145`. En nombres de archivo, `:` se reemplaza por `_`.
- **IDs propios** como slugs en español sin tildes (`via:glucolisis`, `cat:carbohidratos`). Una vez publicados no cambian.
- **Paleta y tipografía** según la sección 8 del manual; colores de evidencia Okabe-Ito y nunca color como único portador de significado.
- **Accesibilidad** WCAG 2.2 AA en todo componente nuevo.

## Organismos

- Fase 0: cuatro organismos — *Escherichia coli* K-12 MG1655 (`taxon:511145`), *Bacillus subtilis* 168 (`taxon:224308`), *Saccharomyces cerevisiae* S288C (`taxon:559292`) y *Homo sapiens* (`taxon:9606`).
- La lista del MVP vive en `pipeline/organismos.yaml`: unos 50 organismos en tres grupos (modelo, clínico, industrial), decidido el 2026-10-08. El código no debe asumir un número fijo.

## Forma de trabajar

- Trabaja **por fases y por tareas pequeñas**. No empieces una fase sin que la anterior cumpla su criterio de avance (sección 16 del manual).
- Antes de escribir código en una tarea nueva, presenta un plan breve: archivos que crearás o modificarás y cómo lo probarás.
- Cada cambio va en una rama y termina en un pull request con: qué se hizo, cómo probarlo y qué quedó pendiente.
- Toda función del pipeline y toda lógica de cobertura lleva pruebas. El algoritmo de cobertura existe en Python y en TypeScript, y ambos pasan el mismo conjunto de casos.
- Las "verdades biológicas" de la sección 14 del manual son pruebas obligatorias; si una falla, investiga y reporta, no ajustes la prueba para que pase.
- Si una URL de descarga, un formato o una licencia no coincide con lo que dice el manual, detente y repórtalo en lugar de improvisar.
- Si necesitas acceso de red a un dominio que el entorno bloquea, dilo explícitamente con el dominio exacto.

## Definición de terminado

Una tarea está terminada cuando: las pruebas pasan, los datos exportados validan contra `schema/`, el linter no reporta errores, la documentación afectada está actualizada y el pull request explica cómo verificar el resultado.

# MetaboAtlas

> Nombre provisional. Proyecto en **Fase 0 (fundamentos)**: todavía no hay sitio publicado ni datos.

MetaboAtlas es una aplicación web pública, gratuita y de código abierto para consultar mapas metabólicos en español. Está pensada para estudiantes y docentes de microbiología, bacteriología, biología, bioquímica, biotecnología y nutrición.

Sigue la lógica de conexiones de KEGG: una **vía de referencia** que se dibuja una sola vez y una **cobertura por organismo** que colorea cada paso según la evidencia de que ese organismo tiene la enzima. A diferencia de KEGG, se construye solo con datos de licencia abierta y explica cada vía por niveles (básico, intermedio y avanzado), citando siempre la base de datos de origen.

## Qué ofrecerá

- Mapas metabólicos dibujados con criterio didáctico (glucólisis, ciclo de Krebs, fermentaciones, β-oxidación, entre otras).
- Cobertura de cada vía en organismos de referencia, calculada a partir de UniProt y Rhea, con niveles de evidencia.
- Fichas de compuesto, reacción, enzima y organismo, con identificadores y enlaces a las bases originales.
- Contenido en tres niveles, glosario, recorrido paso a paso y citación automática.

## Principios

1. **Solo datos abiertos.** Únicamente se redistribuyen datos de fuentes con licencia verificada (CC0, CC BY 4.0 o dominio público), registradas en [`sources.yaml`](sources.yaml).
2. **KEGG, BioCyc/MetaCyc, HMDB, SMPDB y VMH son solo enlaces.** No se descargan ni se copian sus datos ni sus mapas.
3. **Trazabilidad total.** Cada dato lleva su fuente, su identificador, la versión de la base y la fecha de descarga.
4. **"Sin anotación" no es "ausente".** La aplicación nunca afirma que un organismo carece de una vía; dice que no se encontró evidencia.
5. **Costo cero.** Sitio estático en GitHub Pages; sin servidores ni bases de datos en producción.

## Estructura del repositorio

```
metaboatlas/
├─ pipeline/        # Python: descarga, normalización, cobertura y exportación de datos
├─ curation/        # definición manual de vías (YAML) y coordenadas de mapas (JSON)
├─ content/         # contenido didáctico en MDX, en español
├─ schema/          # JSON Schema: contrato entre el pipeline y la web
├─ web/             # sitio estático en Next.js
├─ docs/            # manual técnico de construcción
├─ sources.yaml     # registro de fuentes, licencias y citas
└─ .github/         # flujos de integración y despliegue
```

El diseño completo está en [`docs/MANUAL.md`](docs/MANUAL.md).

## Estado

| Fase | Contenido | Estado |
| --- | --- | --- |
| 0 — Fundamentos | Repositorio, licencias, esquemas, pipeline mínimo, glucólisis con 4 organismos | En curso |
| 1 — MVP público | 10 vías, unos 50 organismos, fichas, buscador, citación | Pendiente |
| 2 — Comparar y conectar | Comparador, mapa general, variantes, modo en vivo | Pendiente |
| 3 — Profundidad | Más vías, cinética, rutas de aprendizaje | Pendiente |
| 4 — Comunidad | Propuestas de docentes, otros idiomas, PWA | Pendiente |

Organismos de la Fase 0: *Escherichia coli* K-12 MG1655, *Bacillus subtilis* 168, *Saccharomyces cerevisiae* S288C y *Homo sapiens*.

## Desarrollo

El pipeline de datos está en [`pipeline/`](pipeline/README.md):

```bash
cd pipeline
uv sync
uv run metabo validate
uv run pytest
```

El sitio está en [`web/`](web/README.md). Necesita el paquete de datos que genera `uv run metabo exportar`:

```bash
cd web
npm ci
npm run dev        # http://localhost:3000/metaboatlas/
```

Los esquemas se validan desde la raíz con `uv run schema/validate_examples.py`. Cada pull request ejecuta estas verificaciones en GitHub Actions ([`checks.yml`](.github/workflows/checks.yml)).

## Publicación

Dos flujos de GitHub Actions publican el sitio, sin servidores propios:

1. **Datos** ([`pipeline.yml`](.github/workflows/pipeline.yml)): una vez al mes, a mano o cuando cambia la curaduría o el pipeline. Descarga las fuentes, exporta el paquete, corre las pruebas con datos reales y lo publica como release `data-AAAA.MM` con su `ATRIBUCION.md`. Las descargas del mes se guardan en la caché de Actions para no repetirlas.
2. **Sitio** ([`web.yml`](.github/workflows/web.yml)): cuando cambia `web/` o termina «Datos». Construye el sitio con el último release `data-*`, revisa la accesibilidad con axe-core y lo publica en GitHub Pages.

Configuración del repositorio, una sola vez:

- Secreto `METABO_CONTACTO` (*Settings → Secrets and variables → Actions*): correo de contacto del User-Agent de las descargas.
- *Settings → Pages → Build and deployment → Source*: **GitHub Actions**.

## Cómo contribuir

Lee [`CONTRIBUTING.md`](CONTRIBUTING.md). Los reportes de errores científicos son especialmente bienvenidos.

## Licencias

- **Código:** [MIT](LICENSE).
- **Contenido didáctico y datos compilados:** [CC BY 4.0](LICENSE-content).
- **Datos de terceros:** cada fuente conserva su propia licencia y su atribución, registradas en [`sources.yaml`](sources.yaml).

## Aviso legal

MetaboAtlas es una herramienta educativa. No tiene uso diagnóstico ni clínico. Los datos provienen de bases de terceros y pueden contener errores u omisiones.

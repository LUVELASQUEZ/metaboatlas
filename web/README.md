# web/

Sitio estático en Next.js (App Router, `output: 'export'`) publicado en GitHub Pages bajo `/metaboatlas` por el flujo `web.yml`. Lee el paquete de datos del pipeline; no tiene servidor ni base de datos.

```bash
npm ci
npm run dev          # copia y valida los datos, y sirve http://localhost:3000/metaboatlas/
npm run build        # sitio estático en out/
npm run lint && npm run typecheck && npm test
npm run a11y         # axe-core sobre out/, en modo claro y oscuro (después de build)
npm run tipos        # regenera lib/tipos/ desde schema/
```

## Datos

`npm run datos` (lo corren `dev` y `build`) busca el paquete más reciente en `../data/<version>/` o en la carpeta que indique `METABO_DATOS`. Valida cada archivo contra `schema/` y lo copia a `public/datos/<version>/`, que no se versiona. Si un archivo no cumple el contrato, la construcción se detiene.

- **Al construir**, las páginas leen la vía, el mapa, los compuestos, las reacciones y las enzimas (`lib/datos.ts`, `lib/vista-via.ts`), además de las licencias y citas de `sources.yaml` (`lib/fuentes.ts`).
- **En el navegador** se descargan bajo demanda la cobertura del organismo elegido y, al abrir la ficha de un paso, los datos de sus enzimas (`lib/cliente.ts`). Las rutas respetan el `basePath` (`lib/rutas.ts`).

`METABO_BASE_PATH` cambia el `basePath` (por omisión, `/metaboatlas`; vacío para servir en la raíz).

## Contrato con el pipeline

- `lib/tipos/` se genera desde `schema/` con `npm run tipos` y no se edita a mano. La CI comprueba que esté al día.
- `lib/cobertura.ts` es el algoritmo de cobertura en TypeScript, gemelo del de `pipeline/metabo/coverage/`. Los dos pasan los casos de `schema/casos/cobertura.json` (`tests/cobertura.test.ts`). Lo usará el modo en vivo de la fase 2; hoy la página muestra la cobertura precalculada.

## Página de una vía (`/via/<slug>/?org=&paso=&compuesto=`)

- **Mapa** (`components/LienzoMapa.tsx`): Cytoscape.js con el diseño `preset`, con las posiciones de `curation/mapas/`. Se descarga solo en las páginas con mapa. Tiene botones para acercar, alejar y ajustar; la rueda del ratón desplaza la página y no hace zoom.
- **Organismo**: el selector recolorea los rótulos según la evidencia y muestra la barra de cobertura con la advertencia didáctica de la sección 5 del manual. Sin organismo, los rótulos usan un tono neutro.
- **Evidencia**: colores Okabe-Ito, siempre con un refuerzo que no es color. Alta lleva borde continuo grueso, media continuo fino, baja discontinuo y sin anotación punteado con "(?)". Los pasos regulados llevan borde grueso y "◆".
- **Ficha** (`components/PanelFicha.tsx`): paso o compuesto elegido, con la fuente, el ID, la versión y la fecha de cada dato. Las proteínas del organismo enlazan a UniProt.
- **Tabla de pasos** (`components/TablaPasos.tsx`): el equivalente accesible del mapa, navegable con teclado.
- **Fuentes**: la caja de la vía y la página `/fuentes/` muestran licencia, versión y cita de cada base, copiadas de `sources.yaml`. Solo se enlazan fuentes verificadas. KEGG, por ejemplo, sigue sin enlace mientras su entrada esté pendiente de verificar.

### Nombres

Mientras no haya nombres en español (vendrán de Wikidata), los compuestos se muestran con el nombre que usa la ecuación de Rhea ("NAD(+)", "dihydroxyacetone phosphate"), que es más legible que el de ChEBI ("NAD(1−)", "glycerone phosphate(2−)"). La ficha muestra los dos. Las enzimas usan el nombre de ENZYME. Nada se traduce a mano.

### Cofactores

Los cofactores de cada paso se escriben junto a su flecha, en el sentido de la vía. Si la flecha va al revés de la reacción maestra de Rhea (como en la fosfoglicerato cinasa), consumidos y producidos se invierten. Se toman de la primera reacción Rhea del paso.

## Pendiente

- Contenido didáctico por niveles, reproductor paso a paso y contador de energía.
- Navegación del mapa con teclado: hoy el equivalente accesible es la tabla de pasos.
- Reversibilidad de las reacciones: no hay fuente verificada, así que todas las flechas tienen una sola punta, en el sentido de la vía.

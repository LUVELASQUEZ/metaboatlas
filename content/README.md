# content/

Contenido didáctico en MDX, en español (licencia CC BY 4.0).

- `vias/`: una vía por archivo, en tres niveles (básico, intermedio, avanzado).
- `glosario/`: un término por archivo.
- `aprender/`: rutas de aprendizaje.
- `preguntas/`: autoevaluación en JSON.

Ver la sección 10 de `docs/MANUAL.md`.

## Formato de una vía

`vias/<slug>.mdx` empieza con un bloque de metadatos YAML:

- `via`: ID de la vía curada (`via:glucolisis`).
- `estado_editorial`: `borrador`, `revisado` o `validado`. Los dos últimos exigen al menos un nombre en `revisores`.
- `generado_con_ia`: `true` mientras el texto redactado con apoyo de IA no se haya revisado.
- `actualizado`: fecha AAAA-MM-DD.
- `pasos`: un texto corto por cada paso de la vía curada (ni uno más ni uno menos). Se muestra en la ficha del paso.

El cuerpo usa estos componentes:

- `<Nivel nivel="basico|intermedio|avanzado">`: los tres son obligatorios. La página muestra solo el nivel elegido.
- `<BalanceEnergetico duplicados={["p06", …]} />`: tabla calculada de la `energia` de la curaduría. `duplicados` son los pasos que ocurren dos veces por molécula de sustrato.
- `<Autoevaluacion />`: lugar donde se muestran las preguntas de `preguntas/<slug>.json`.
- `<RefPendiente nota="…" />`: marca una afirmación que espera su referencia. Nunca se escriben citas de memoria (regla 6 de CLAUDE.md).

`web/tests/contenido.test.ts` comprueba cada archivo contra `curation/vias/` y verifica que el balance coincida con lo que dice el texto.

## Glosario

`glosario/<termino>.mdx` (el nombre del archivo es un slug sin tildes) lleva en sus metadatos `termino`, `breve`, `formas`, `vias`, `estado_editorial`, `generado_con_ia`, `revisores` y `actualizado`. El cuerpo tiene la definición ampliada y un ejemplo.

`formas` son las maneras en que el término aparece en un texto, sin distinguir mayúsculas. La primera aparición en cada nivel de una vía se enlaza sola a la ficha del término (nunca dentro de títulos ni enlaces). Una forma no puede pertenecer a dos términos.

## Preguntas

`preguntas/<slug>.json` lleva los mismos metadatos editoriales y una lista `preguntas`. Cada pregunta tiene `id`, `nivel`, `enunciado`, `explicacion` y un `tipo`:

- `opcion_multiple`: `opciones` y `correcta` (índice desde 0).
- `ordenar_pasos`: `pasos` en el orden correcto, que debe ser el de la curaduría.

El campo opcional `verifica` guarda los datos con que `web/tests/glosario-preguntas.test.ts` comprueba la respuesta contra la curaduría (balance, pasos regulados, EC). Los resultados se corrigen en el navegador y no se guardan.

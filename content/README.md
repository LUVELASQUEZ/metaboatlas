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
- `<RefPendiente nota="…" />`: marca una afirmación que espera su referencia. Nunca se escriben citas de memoria (regla 6 de CLAUDE.md).

`web/tests/contenido.test.ts` comprueba cada archivo contra `curation/vias/` y verifica que el balance coincida con lo que dice el texto.

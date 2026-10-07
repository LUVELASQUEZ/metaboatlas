# curation/vias/

Un archivo `<slug>.yaml` por vía con módulos, pasos, IDs Rhea y números EC. Sigue la estructura de [`schema/via.schema.json`](../../schema/via.schema.json). Los identificadores se completan a partir de datos descargados, nunca de memoria.

## Cómo se cura una vía

Desde `pipeline/`, con Rhea, ENZYME y ChEBI descargados (`uv run metabo extraer rhea|enzyme|chebi`):

1. Busca el número EC de cada paso por su nombre en `enzyme.dat` y confirma que está vigente.
2. `uv run metabo curar buscar <EC>` lista las reacciones maestras de Rhea asociadas a ese EC, con su ecuación y el nombre de cada participante ChEBI. Elige la reacción del paso leyendo la ecuación y copia la ecuación como comentario en el YAML.
3. Anota en `fuentes` las versiones de Rhea, ENZYME y ChEBI con las que verificaste.
4. `uv run metabo curar validar` comprueba que cada RHEA exista, sea la reacción maestra y esté asociado en `rhea2ec` a un EC del paso; que cada EC esté vigente en ENZYME; que cada participante exista en ChEBI, y que `fuentes` coincida con lo descargado.

Las pruebas (`pytest`) revisan en cada PR la estructura de estas vías sin usar la red: esquema, un módulo por paso y `orden` sin huecos. La verificación de IDs necesita los datos descargados y se ejecuta con `curar validar`.

Una vía nueva entra como `estado_editorial: borrador` hasta que una persona la revise.

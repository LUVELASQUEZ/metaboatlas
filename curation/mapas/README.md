# curation/mapas/

Un archivo `<slug>.json` por vía con el dibujo de su mapa. Su formato es [`schema/mapa.schema.json`](../../schema/mapa.schema.json). `uv run metabo exportar` lo verifica y lo copia como `mapas/<slug>.json` en el paquete de datos. Una vía sin mapa se exporta igual, y la web la dibujará con un diseño automático.

El mapa guarda **solo posiciones**, en píxeles de un lienzo con el origen arriba a la izquierda. Los nombres, las reacciones y la evidencia se toman del paquete de datos, así que el mapa no se desactualiza cuando cambian los datos.

- `compuestos`: un nodo por metabolito principal, con el lado donde va su nombre (`etiqueta`).
- `pasos`: una flecha por paso, `desde` → `hacia`, en el sentido de la vía. Lleva la posición del rótulo de la enzima y el lado donde se dibujan los cofactores.
- `modulos`: el rectángulo de fondo de cada módulo.
- `portales`: rótulos que llevan a vías conectadas (vacío mientras haya una sola vía).

## Qué se verifica al exportar

- Que el archivo cumpla el esquema y sea de la vía con el mismo slug.
- Que todo quede dentro del lienzo.
- Que cada paso y cada módulo se dibujen exactamente una vez.
- Que ningún nodo se repita ni sea un cofactor de `curation/compuestos.yaml`. Los cofactores (ATP, NAD⁺, H⁺, agua…) se dibujan junto a la flecha, como en los mapas de los libros de texto.
- Que cada flecha corresponda a lados opuestos de una reacción Rhea de su paso, en cualquier sentido.

Un nodo puede mostrar un compuesto más general que el participante de Rhea, siempre que ChEBI diga que el participante "es un" ese compuesto o que es su ácido o base conjugado. Por ejemplo, en la glucólisis el nodo de la glucosa 6-fosfato es `CHEBI:61548` (D-glucopyranose 6-phosphate(2−)). La hexocinasa (`RHEA:17825`) lo produce tal cual, pero la isomerasa (`RHEA:11816`) consume su anómero alfa, `CHEBI:58225`, que en ChEBI "es un" `CHEBI:61548`. Así el compuesto se dibuja una sola vez.

## Cómo editar un mapa

1. Mueve coordenadas en el JSON. La glucólisis usa una columna vertical (de arriba abajo) con módulos de fondo para la fase preparatoria y la de beneficio.
2. Corre `uv run metabo exportar`: si una flecha no corresponde a su reacción, falla y dice cuál.
3. Mira el resultado en la web (o en la vista previa del PR mientras no exista la web).

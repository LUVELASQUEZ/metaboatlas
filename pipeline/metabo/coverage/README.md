# pipeline/metabo/coverage/

Algoritmo de cobertura por paso y por vía (sección 5 de `docs/MANUAL.md`). Debe pasar el mismo conjunto de casos que la implementación TypeScript de `web/lib/`: [`schema/casos/cobertura.json`](../../../schema/casos/cobertura.json).

- `algorithm.py`: las reglas, sin lectura de archivos.
- `proteome.py`: lee `raw/uniprot/<release>/<UP>.tsv.gz` (columnas `Entry`, `Reviewed`, `EC number`, `Rhea ID`).
- `compute.py`: arma la cobertura de cada vía curada en cada organismo, la valida contra `schema/cobertura.schema.json` y la escribe en `data/<version_datos>/cobertura/<slug>/<taxon>.json`.

## Reglas por paso

En este orden; gana la primera que se cumple:

| Estado | Regla | ¿Suma al porcentaje? |
| --- | --- | --- |
| `espontaneo` | El paso no requiere enzima | Sí |
| `alta` | Una proteína revisada (Swiss-Prot) del proteoma tiene una reacción Rhea del paso | Sí |
| `media` | Una proteína no revisada (TrEMBL) tiene una reacción Rhea del paso | Sí |
| `baja` | Una proteína tiene uno de los números EC del paso | No (es "probable") |
| `sin_anotacion` | Nada de lo anterior. Nunca se dice "ausente" | No |

- **Rhea maestro.** UniProt anota muchas veces la dirección fisiológica de una reacción (ID LR o RL). Se convierte a la reacción maestra con `rhea-directions.tsv`, porque la curaduría usa IDs maestros.
- **EC exacto.** Solo coincide un EC completo; un EC parcial de UniProt (`2.7.1.-`) no cuenta.
- **Proteínas citadas.** Las que respaldan el estado ganador: solo las revisadas en `alta`, las no revisadas en `media` y todas las que tienen el EC en `baja`. Ordenadas y sin repetir.
- **Complejos.** Si el paso tiene `complejo: true`, basta una subunidad anotada y se agrega la advertencia `complejo_verificar_subunidades`.

## Cobertura de la vía

`cobertura` = pasos `espontaneo`, `alta` o `media` / pasos totales × 100, redondeada a un decimal. La clase se decide con los umbrales de `pipeline/config.yaml` comparando con enteros (4 de 5 pasos es exactamente 80 %): `completa` ≥ 100, `casi_completa` ≥ 80, `parcial` ≥ 30 y `no_detectada` por debajo.

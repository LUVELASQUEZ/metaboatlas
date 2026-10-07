// Balance energético de una vía a partir de la curaduría (`energia` de cada paso).
import type { Via } from "@/lib/tipos/via";

export interface FilaBalance {
  molecula: string;
  consumidas: number;
  producidas: number;
  neto: number;
}

/**
 * Suma los cambios de cada paso por cada molécula de sustrato inicial. Los pasos de
 * `duplicados` ocurren dos veces (en la glucólisis, los de las dos triosas fosfato).
 */
export function balanceEnergetico(pasos: Via["pasos"], duplicados: readonly string[] = []): FilaBalance[] {
  const desconocidos = duplicados.filter((id) => !pasos.some((p) => p.id === id));
  if (desconocidos.length > 0) throw new Error(`Pasos inexistentes en el balance: ${desconocidos.join(", ")}`);
  const filas = new Map<string, FilaBalance>();
  for (const paso of pasos) {
    const veces = duplicados.includes(paso.id) ? 2 : 1;
    for (const [molecula, cambio] of Object.entries(paso.energia ?? {})) {
      const fila = filas.get(molecula) ?? { molecula, consumidas: 0, producidas: 0, neto: 0 };
      if (cambio < 0) fila.consumidas += -cambio * veces;
      else fila.producidas += cambio * veces;
      fila.neto += cambio * veces;
      filas.set(molecula, fila);
    }
  }
  return [...filas.values()];
}

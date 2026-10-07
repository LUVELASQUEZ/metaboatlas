// Color y patrón de cada estado de evidencia (sección 7 de docs/MANUAL.md). El
// patrón del borde repite lo que dice el color, para no depender solo de él.
import type { Estado } from "@/lib/cobertura";

export interface EstiloEvidencia {
  variable: string;
  borde: "solid" | "dashed" | "dotted";
  ancho: number;
}

export const ESTILO_EVIDENCIA: Record<Estado | "neutro", EstiloEvidencia> = {
  alta: { variable: "--ev-alta", borde: "solid", ancho: 3 },
  media: { variable: "--ev-media", borde: "solid", ancho: 1.5 },
  baja: { variable: "--ev-baja", borde: "dashed", ancho: 2.5 },
  sin_anotacion: { variable: "--ev-sin-anotacion", borde: "dotted", ancho: 2 },
  espontaneo: { variable: "--ev-espontaneo", borde: "dotted", ancho: 1 },
  neutro: { variable: "--ev-neutro", borde: "solid", ancho: 1.5 },
};

/** Marca de texto de los pasos regulados (puntos de control). */
export const MARCA_REGULADO = "◆";

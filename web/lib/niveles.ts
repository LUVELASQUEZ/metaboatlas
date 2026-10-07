// Niveles didácticos (sección 10 de docs/MANUAL.md). El nivel vive en la URL (?nivel=).
export const NIVELES = ["basico", "intermedio", "avanzado"] as const;
export type Nivel = (typeof NIVELES)[number];

export const NOMBRE_NIVEL: Record<Nivel, string> = {
  basico: "Básico",
  intermedio: "Intermedio",
  avanzado: "Avanzado",
};

export const PREGUNTA_NIVEL: Record<Nivel, string> = {
  basico: "¿Qué hace y para qué sirve?",
  intermedio: "¿Cómo funciona?",
  avanzado: "¿Qué dicen los datos?",
};

// Quien llega por primera vez empieza por lo básico (flujo 1 de la sección 9).
export const NIVEL_INICIAL: Nivel = "basico";

/** En el nivel básico el mapa oculta los números EC y los cofactores. */
export const mapaDetallado = (nivel: Nivel) => nivel !== "basico";

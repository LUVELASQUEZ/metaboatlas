// Textos de la interfaz sobre evidencia y cobertura (secciones 5 y 7 de docs/MANUAL.md).
import type { Clase, Estado } from "@/lib/cobertura";

export const ESTADOS: readonly Estado[] = ["alta", "media", "baja", "sin_anotacion", "espontaneo"];

export const NOMBRE_ESTADO: Record<Estado, string> = {
  alta: "Evidencia alta",
  media: "Evidencia media",
  baja: "Evidencia baja",
  sin_anotacion: "Sin anotación",
  espontaneo: "Espontáneo",
};

export const EXPLICACION_ESTADO: Record<Estado, string> = {
  alta: "Una proteína revisada (Swiss-Prot) del organismo está anotada con la reacción Rhea del paso.",
  media:
    "Solo proteínas no revisadas (TrEMBL, anotación automática) están anotadas con la reacción Rhea del paso.",
  baja: "Una proteína del organismo tiene el número EC del paso, pero no la reacción Rhea. Es probable; no suma a la cobertura.",
  sin_anotacion:
    "No encontramos evidencia en las bases de datos. No significa que el organismo carezca de la enzima.",
  espontaneo: "El paso ocurre sin enzima y siempre cuenta como presente.",
};

/** Refuerzo no cromático de cada estado en el mapa y la leyenda. */
export const PATRON_ESTADO: Record<Estado, string> = {
  alta: "borde continuo grueso",
  media: "borde continuo fino",
  baja: "borde discontinuo",
  sin_anotacion: "borde punteado y signo de interrogación",
  espontaneo: "flecha punteada",
};

export const NOMBRE_CLASE: Record<Clase, string> = {
  completa: "Completa",
  casi_completa: "Casi completa",
  parcial: "Parcial",
  no_detectada: "No detectada",
};

// Mensajes de la tabla de clases de la sección 5 del manual.
export const MENSAJE_CLASE: Record<Clase, string> = {
  completa: "Este organismo tiene todas las enzimas de la vía.",
  casi_completa: "Faltan pasos sin anotar; pueden existir enzimas no caracterizadas.",
  parcial: "El organismo tiene parte de la vía; puede usar una variante.",
  no_detectada: "No encontramos evidencia de esta vía en este organismo.",
};

// Advertencia didáctica obligatoria de la sección 5 del manual.
export const ADVERTENCIA_COBERTURA =
  "La cobertura se calcula a partir de anotaciones en bases de datos. Un paso sin anotación puede deberse a una enzima aún no caracterizada.";

export const NOMBRE_EDITORIAL = {
  borrador: "Borrador",
  revisado: "Revisado",
  validado: "Validado",
} as const;

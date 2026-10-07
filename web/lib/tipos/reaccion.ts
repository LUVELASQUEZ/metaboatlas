// Generado por scripts/generate-types.mjs desde schema/. No editar a mano.

/**
 * Referencias a MetaCyc, Reactome y KEGG como pares (fuente, id).
 */
export type Xrefs = Xref[];
/**
 * @minItems 1
 */
export type ListaProcedencia = [Procedencia, ...Procedencia[]];

/**
 * Ficha de una reacción Rhea (ID maestro). Archivo reacciones/RHEA_<n>.json del paquete de datos (secciones 3 y 4 de docs/MANUAL.md).
 */
export interface Reaccion {
  /**
   * ID maestro (sin dirección) de Rhea.
   */
  id: string;
  /**
   * Ecuación textual tal como la publica Rhea.
   */
  ecuacion: string;
  /**
   * @minItems 2
   */
  participantes: [Participante, Participante, ...Participante[]];
  /**
   * IDs Rhea de las tres variantes de dirección de la reacción maestra.
   */
  direcciones: {
    izquierda_a_derecha: string;
    derecha_a_izquierda: string;
    bidireccional: string;
  };
  /**
   * Reversibilidad en condiciones fisiológicas; null si no hay fuente que la respalde.
   */
  reversible: boolean | null;
  es_transporte: boolean;
  /**
   * Items: Slug en español, sin tildes, en minúsculas y con guiones.
   */
  compartimento?: string[];
  /**
   * Items: Número EC completo o parcial (EC:2.7.1.1, EC:2.7.1.-, EC:3.5.1.n3).
   */
  ec: string[];
  /**
   * Energía libre estándar, solo si hay una fuente que la respalde.
   */
  delta_g?: null | {
    valor: number;
    unidad: "kJ/mol";
    procedencia: Procedencia;
  };
  xrefs: Xrefs;
  procedencia: ListaProcedencia;
}
export interface Participante {
  compuesto: string;
  lado: "izquierda" | "derecha";
  /**
   * Coeficiente estequiométrico. Rhea usa coeficientes como 'n' o '2n' en polímeros.
   */
  estequiometria: number | string;
  /**
   * Compartimento del participante (útil en reacciones de transporte).
   */
  compartimento?: string;
}
/**
 * De dónde sale un dato: fuente, ID en esa fuente, versión de la base y fecha de descarga.
 */
export interface Procedencia {
  /**
   * Clave de una fuente registrada en sources.yaml (rhea, chebi, uniprot, …).
   */
  fuente: string;
  /**
   * ID nativo del registro en la fuente, sin prefijo CURIE (por ejemplo 15361 en ChEBI o P0A6T1 en UniProt).
   */
  id: string;
  version: string;
  /**
   * Fecha ISO 8601 (AAAA-MM-DD).
   */
  fecha_descarga: string;
}
/**
 * Referencia cruzada como par (fuente, id). El enlace se construye con la plantilla `tipo` de la fuente en sources.yaml, reemplazando {id}.
 */
export interface Xref {
  /**
   * Clave de una fuente registrada en sources.yaml (rhea, chebi, uniprot, …).
   */
  fuente: string;
  /**
   * Clave de la plantilla de URL en sources.yaml (por ejemplo via_referencia en KEGG).
   */
  tipo: string;
  /**
   * ID nativo en la fuente, sin prefijo CURIE (por ejemplo map00010, C00022, 2.7.1.1).
   */
  id: string;
}

// Generado por scripts/generate-types.mjs desde schema/. No editar a mano.

export type Xrefs = Xref[];
/**
 * @minItems 1
 */
export type ListaProcedencia = [Procedencia, ...Procedencia[]];
/**
 * Referencias a ENZYME, BRENDA y KEGG como pares (fuente, id).
 */
export type Xrefs1 = Xref[];

/**
 * Ficha de una actividad enzimática identificada por su número EC, con las proteínas que la tienen en cada organismo. Archivo enzimas/EC_<n>.json del paquete de datos (sección 4 de docs/MANUAL.md).
 */
export interface EnzimaActividad {
  /**
   * Número EC completo o parcial (EC:2.7.1.1, EC:2.7.1.-, EC:3.5.1.n3).
   */
  id: string;
  nombre: TextoBilingue;
  nombres_alternativos: string[];
  /**
   * Clase EC principal (1 oxidorreductasas … 7 translocasas).
   */
  clase: number;
  /**
   * Reacción catalizada, tal como la publica ENZYME.
   */
  reaccion?: string | null;
  cofactores: string[];
  /**
   * Estado del número EC en ENZYME.
   */
  estado: "vigente" | "transferido" | "eliminado";
  /**
   * Items: Número EC completo o parcial (EC:2.7.1.1, EC:2.7.1.-, EC:3.5.1.n3).
   */
  transferido_a?: string[];
  /**
   * Reacciones Rhea asociadas a este número EC.
   */
  reacciones: string[];
  /**
   * Proteínas anotadas con esta actividad en los organismos precalculados.
   */
  proteinas: Proteina[];
  xrefs: Xrefs1;
  procedencia: ListaProcedencia;
}
/**
 * Nombre aceptado (ENZYME, en inglés) y su nombre en español.
 */
export interface TextoBilingue {
  es: string | null;
  en: string;
}
/**
 * Proteína concreta de un organismo (UniProtKB).
 */
export interface Proteina {
  /**
   * Accesión UniProtKB con prefijo UNIPROT.
   */
  id: string;
  /**
   * Identificador de NCBI Taxonomy.
   */
  taxon: string;
  nombre?: string | null;
  genes: string[];
  /**
   * Items: Número EC completo o parcial (EC:2.7.1.1, EC:2.7.1.-, EC:3.5.1.n3).
   */
  ec: string[];
  rhea: string[];
  /**
   * true si es Swiss-Prot; false si es TrEMBL.
   */
  revisada: boolean;
  puntaje_anotacion?: number | null;
  xrefs?: Xrefs;
  procedencia: ListaProcedencia;
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

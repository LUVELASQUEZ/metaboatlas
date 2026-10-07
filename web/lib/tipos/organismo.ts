// Generado por scripts/generate-types.mjs desde schema/. No editar a mano.

export type Xrefs = Xref[];
/**
 * @minItems 1
 */
export type ListaProcedencia = [Procedencia, ...Procedencia[]];

/**
 * Perfil de un organismo (NCBI Taxonomy + proteoma de UniProt). Archivo organismos/<taxon>.json del paquete de datos (sección 4 de docs/MANUAL.md).
 */
export interface Organismo {
  /**
   * Identificador de NCBI Taxonomy.
   */
  id: string;
  nombre_cientifico: string;
  cepa: string | null;
  nombre_comun?: TextoBilingue | null;
  /**
   * Rango taxonómico según NCBI (species, strain, …).
   */
  rango: string;
  /**
   * Linaje desde la raíz hasta el padre inmediato.
   */
  linaje: {
    /**
     * Identificador de NCBI Taxonomy.
     */
    taxon: string;
    nombre: string;
    rango: string;
  }[];
  dominio: "bacteria" | "arquea" | "eucariota";
  /**
   * Tinción de Gram. 'no_aplica' en organismos que no son bacterias; null si no hay dato con fuente.
   */
  gram: "positivo" | "negativo" | "variable" | "no_aplica" | null;
  /**
   * ID del proteoma de referencia en UniProt.
   */
  proteoma_referencia: string | null;
  intereses: ("modelo" | "clinico" | "industrial")[];
  /**
   * Código de organismo de KEGG obtenido de las referencias cruzadas de UniProt (solo para construir enlaces).
   */
  codigo_kegg: string | null;
  xrefs: Xrefs;
  procedencia: ListaProcedencia;
}
/**
 * Texto en español e inglés. Si falta el español, `es` es null y queda marcado para traducción manual.
 */
export interface TextoBilingue {
  es: string | null;
  en: string;
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

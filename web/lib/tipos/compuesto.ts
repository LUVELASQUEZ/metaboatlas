// Generado por scripts/generate-types.mjs desde schema/. No editar a mano.

/**
 * Referencias a KEGG, HMDB, PubChem y Wikidata como pares (fuente, id).
 */
export type Xrefs = Xref[];
/**
 * @minItems 1
 */
export type ListaProcedencia = [Procedencia, ...Procedencia[]];

/**
 * Ficha de un compuesto químico (ChEBI). Archivo compuestos/CHEBI_<n>.json del paquete de datos (sección 4 de docs/MANUAL.md).
 */
export interface Compuesto {
  id: string;
  nombre: TextoBilingue;
  /**
   * Definición de ChEBI, en inglés.
   */
  definicion?: string | null;
  sinonimos: string[];
  /**
   * Fórmula molecular tal como la publica ChEBI (la web la muestra con subíndices).
   */
  formula: string | null;
  carga: number | null;
  masa_monoisotopica: number | null;
  smiles: string | null;
  inchi: string | null;
  inchikey: string | null;
  /**
   * Clase de molécula derivada de la ontología de ChEBI; define el color en el mapa.
   */
  clase: "carbohidrato" | "lipido" | "aminoacido" | "nucleotido" | "cofactor" | "ion_gas" | "otro";
  /**
   * true si es cofactor o metabolito 'moneda' (ATP, NAD+, CoA, …).
   */
  es_cofactor: boolean;
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

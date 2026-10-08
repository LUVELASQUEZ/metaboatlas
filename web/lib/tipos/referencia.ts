// Generado por scripts/generate-types.mjs desde schema/. No editar a mano.

export type Xrefs = Xref[];
/**
 * @minItems 1
 */
export type ListaProcedencia = [Procedencia, ...Procedencia[]];

/**
 * Datos de cita de un artículo citado en el contenido didáctico (curation/referencias.yaml + Europe PMC). Solo datos de cita: ni resúmenes ni texto del artículo. Archivo referencias/PMID_<n>.json del paquete de datos.
 */
export interface ReferenciaBibliografica {
  id: string;
  titulo: string;
  /**
   * Lista de autores tal como la da Europe PMC ("Park JO, Rubin SA, …").
   */
  autores: string;
  revista: string;
  anio: number;
  volumen: string | null;
  numero: string | null;
  paginas: string | null;
  doi: string | null;
  /**
   * ID en PubMed Central; si existe, el artículo se puede leer gratis.
   */
  pmcid: string | null;
  /**
   * Europe PMC lo marca como de acceso abierto (licencia que permite reutilizarlo).
   */
  acceso_abierto: boolean;
  /**
   * Qué afirmación del contenido respalda (curation/referencias.yaml).
   */
  respalda: string;
  /**
   * Dónde se comprobó que el artículo respalda la afirmación.
   */
  verificado: "resumen" | "texto completo";
  xrefs: Xrefs;
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

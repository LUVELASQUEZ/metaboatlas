// Generado por scripts/generate-types.mjs desde schema/. No editar a mano.

/**
 * Cobertura de una vía en un organismo, con el estado de evidencia de cada paso. Archivo cobertura/<slug>/<taxon>.json del paquete de datos (sección 5 de docs/MANUAL.md). 'Sin anotación' no significa 'ausente'.
 */
export interface Cobertura {
  /**
   * ID propio de una vía, por ejemplo via:glucolisis.
   */
  via: string;
  /**
   * Identificador de NCBI Taxonomy.
   */
  taxon: string;
  /**
   * Porcentaje de pasos presentes o espontáneos.
   */
  cobertura: number;
  clase: "completa" | "casi_completa" | "parcial" | "no_detectada";
  /**
   * Estado de cada paso, por ID local del paso.
   */
  pasos: {
    [k: string]: EstadoPaso;
  };
  /**
   * precalculado en el pipeline o calculado en vivo en el navegador.
   */
  modo?: "precalculado" | "en_vivo";
  /**
   * Fecha ISO 8601 (AAAA-MM-DD).
   */
  calculado: string;
  fuentes: VersionesFuentes;
}
export interface EstadoPaso {
  /**
   * Estado de un paso en un organismo (sección 5). Nunca existe el estado 'ausente'.
   */
  estado: "espontaneo" | "alta" | "media" | "baja" | "sin_anotacion";
  /**
   * Proteínas del organismo que respaldan el estado.
   *
   * Items: Accesión UniProtKB con prefijo UNIPROT.
   */
  proteinas: string[];
  advertencias?: "complejo_verificar_subunidades"[];
}
/**
 * Versión de cada fuente usada, por clave de sources.yaml.
 */
export interface VersionesFuentes {
  [k: string]: string;
}

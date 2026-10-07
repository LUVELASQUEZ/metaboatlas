// Generado por scripts/generate-types.mjs desde schema/. No editar a mano.

/**
 * Procedencia del paquete de datos: cada descarga con su fuente, URL, versión, fecha, licencia y checksum SHA-256 (regla 4 de CLAUDE.md, sección 6 de docs/MANUAL.md).
 */
export interface Manifiesto {
  /**
   * Versión del paquete de datos de MetaboAtlas (AAAA.MM).
   */
  version_datos: string;
  /**
   * Fecha y hora UTC en que se escribió el manifiesto (ISO 8601).
   */
  generado: string;
  descargas: Descarga[];
}
export interface Descarga {
  /**
   * Clave de una fuente registrada en sources.yaml (rhea, chebi, uniprot, …).
   */
  fuente: string;
  url: string;
  /**
   * Versión de la base según la fuente (por ejemplo, el número de release).
   */
  version: string;
  /**
   * Fecha ISO 8601 (AAAA-MM-DD).
   */
  fecha_descarga: string;
  /**
   * Ruta del archivo dentro del directorio de datos crudos: <fuente>/<version>/<nombre>.
   */
  archivo: string;
  sha256: string;
  bytes: number;
  licencia: string;
}

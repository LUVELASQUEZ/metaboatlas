// Toda ruta interna y todo fetch de JSON pasan por aquí para respetar el basePath
// de GitHub Pages (/metaboatlas). Los <Link> de Next.js ya lo agregan solos.
export const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

export function conBase(ruta: string): string {
  return `${BASE_PATH}${ruta}`;
}

/** URL pública de un archivo del paquete de datos, p. ej. cobertura/glucolisis/9606.json. */
export function urlDatos(version: string, archivo: string): string {
  return conBase(`/datos/${version}/${archivo}`);
}

/** Nombre de archivo de un CURIE: `:` se reemplaza por `_` (CHEBI:15361 -> CHEBI_15361). */
export function archivoDe(curie: string): string {
  return curie.replace(":", "_");
}

/** ID nativo de un CURIE (CHEBI:15361 -> 15361; via:glucolisis -> glucolisis). */
export function nativo(curie: string): string {
  return curie.slice(curie.indexOf(":") + 1);
}

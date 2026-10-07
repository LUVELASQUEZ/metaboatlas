// Descargas del paquete de datos desde el navegador, con caché en memoria.
import { urlDatos, archivoDe, nativo } from "@/lib/rutas";
import type { Cobertura } from "@/lib/tipos/cobertura";
import type { EnzimaActividad } from "@/lib/tipos/enzima";

const cache = new Map<string, Promise<unknown>>();

function descargar<T>(url: string): Promise<T> {
  let pendiente = cache.get(url);
  if (!pendiente) {
    pendiente = fetch(url).then((r) => {
      if (!r.ok) throw new Error(`No se pudo descargar ${url} (${r.status}).`);
      return r.json();
    });
    pendiente.catch(() => cache.delete(url));
    cache.set(url, pendiente);
  }
  return pendiente as Promise<T>;
}

export function descargarCobertura(version: string, slug: string, taxon: string) {
  return descargar<Cobertura>(urlDatos(version, `cobertura/${slug}/${nativo(taxon)}.json`));
}

export function descargarEnzima(version: string, ec: string) {
  return descargar<EnzimaActividad>(urlDatos(version, `enzimas/${archivoDe(ec)}.json`));
}

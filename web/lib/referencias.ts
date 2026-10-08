// Referencias bibliográficas del contenido (<Ref pmid="…" /> en el MDX). Los datos de
// cita vienen del paquete (Europe PMC); la lista de PMID permitidos, de
// curation/referencias.yaml.
import { readFileSync } from "node:fs";
import path from "node:path";
import { parse } from "yaml";
import type { ReferenciaBibliografica } from "@/lib/tipos/referencia";

const REF = /<Ref\s+pmid="([^"]*)"\s*\/>/g;

/** PMID de un atributo `pmid` ("27159581 17158705" admite varios). */
export function separarPmids(valor: string): string[] {
  return valor.split(/\s+/).filter(Boolean);
}

/** PMID citados en el MDX, en orden de primera aparición: su posición da el número. */
export function pmidsCitados(cuerpo: string): string[] {
  const vistos: string[] = [];
  for (const [, valor] of cuerpo.matchAll(REF)) {
    for (const pmid of separarPmids(valor!)) if (!vistos.includes(pmid)) vistos.push(pmid);
  }
  return vistos;
}

/** PMID curados en curation/referencias.yaml. */
export function pmidsCurados(raiz = path.join(process.cwd(), "..")): string[] {
  const datos = parse(readFileSync(path.join(raiz, "curation", "referencias.yaml"), "utf8")) as {
    referencias?: { pmid: string }[];
  };
  return (datos.referencias ?? []).map((r) => String(r.pmid));
}

/** "Park JO, Rubin SA. Título. Nat Chem Biol. 2016;12(7):482-489." */
export function textoCita(r: ReferenciaBibliografica): string {
  const autores = r.autores.replace(/\.$/, "");
  const titulo = r.titulo.replace(/\.$/, "");
  const numero = r.numero ? `(${r.numero})` : "";
  const volumen = r.volumen ? `;${r.volumen}${numero}` : "";
  const paginas = r.paginas ? `:${r.paginas}` : "";
  return `${autores ? `${autores}. ` : ""}${titulo}. ${r.revista}. ${r.anio}${volumen}${paginas}.`;
}

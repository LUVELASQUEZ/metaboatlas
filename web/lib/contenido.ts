// Contenido didáctico de las vías (content/vias/<slug>.mdx, sección 10 de docs/MANUAL.md).
// Se lee y compila al construir el sitio; el navegador recibe HTML ya renderizado.
import { evaluate } from "@mdx-js/mdx";
import type { MDXContent } from "mdx/types";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import * as runtime from "react/jsx-runtime";
import remarkGfm from "remark-gfm";
import { parse } from "yaml";
import { NIVELES } from "@/lib/niveles";
import type { Via } from "@/lib/tipos/via";

export const ESTADOS_EDITORIALES = ["borrador", "revisado", "validado"] as const;

export interface MetaContenido {
  via: string;
  estado_editorial: (typeof ESTADOS_EDITORIALES)[number];
  generado_con_ia: boolean;
  revisores: string[];
  actualizado: string;
  pasos: Record<string, string>;
}

export interface ContenidoVia {
  meta: MetaContenido;
  cuerpo: string;
}

export const DIR_CONTENIDO = path.join(process.cwd(), "..", "content");

/** Lee content/vias/<slug>.mdx; null si la vía aún no tiene contenido. */
export function leerContenidoVia(slug: string, raiz = DIR_CONTENIDO): ContenidoVia | null {
  const archivo = path.join(raiz, "vias", `${slug}.mdx`);
  if (!existsSync(archivo)) return null;
  const texto = readFileSync(archivo, "utf8");
  const partes = /^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/.exec(texto);
  const [, metadatos, cuerpo] = partes ?? [];
  if (metadatos === undefined || cuerpo === undefined) {
    throw new Error(`${archivo}: falta el bloque de metadatos (---).`);
  }
  return { meta: parse(metadatos) as MetaContenido, cuerpo };
}

/** Problemas del contenido frente a la vía curada; vacío si todo está bien. */
export function validarContenido(contenido: ContenidoVia, via: Via): string[] {
  const { meta, cuerpo } = contenido;
  const errores: string[] = [];
  if (meta.via !== via.id) errores.push(`via es ${meta.via}, se esperaba ${via.id}`);
  if (!ESTADOS_EDITORIALES.includes(meta.estado_editorial)) {
    errores.push(`estado_editorial desconocido: ${meta.estado_editorial}`);
  }
  if (typeof meta.generado_con_ia !== "boolean") errores.push("generado_con_ia debe ser true o false");
  if (!Array.isArray(meta.revisores)) errores.push("revisores debe ser una lista");
  if (meta.estado_editorial !== "borrador" && (meta.revisores?.length ?? 0) === 0) {
    errores.push(`un contenido ${meta.estado_editorial} necesita al menos un revisor`);
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(meta.actualizado))) errores.push("actualizado debe ser AAAA-MM-DD");
  const pasos = meta.pasos ?? {};
  for (const p of via.pasos) {
    const texto = pasos[p.id];
    if (typeof texto !== "string" || texto.trim() === "") errores.push(`falta el texto del paso ${p.id}`);
  }
  for (const id of Object.keys(pasos)) {
    if (!via.pasos.some((p) => p.id === id)) errores.push(`texto para un paso que no existe: ${id}`);
  }
  for (const nivel of NIVELES) {
    if (!cuerpo.includes(`<Nivel nivel="${nivel}">`)) errores.push(`falta el nivel ${nivel}`);
  }
  return errores;
}

/** Compila el MDX a un componente de React. */
export async function compilarContenido(cuerpo: string): Promise<MDXContent> {
  const modulo = await evaluate(cuerpo, { ...runtime, remarkPlugins: [remarkGfm] });
  return modulo.default;
}

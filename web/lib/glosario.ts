// Glosario (content/glosario/<termino>.mdx, sección 10 de docs/MANUAL.md).
import { readdirSync } from "node:fs";
import path from "node:path";
import { DIR_CONTENIDO, ESTADOS_EDITORIALES, leerMdx } from "@/lib/contenido";

export interface Termino {
  id: string;
  termino: string;
  /** Formas en que aparece en un texto; la primera aparición se enlaza al glosario. */
  formas: string[];
  breve: string;
  vias: string[];
  estado_editorial: (typeof ESTADOS_EDITORIALES)[number];
  generado_con_ia: boolean;
  revisores: string[];
  actualizado: string;
  cuerpo: string;
}

/** Todos los términos, en orden alfabético. */
export function leerGlosario(raiz = DIR_CONTENIDO): Termino[] {
  const dir = path.join(raiz, "glosario");
  return readdirSync(dir)
    .filter((f) => f.endsWith(".mdx"))
    .map((f) => {
      const { meta, cuerpo } = leerMdx(path.join(dir, f));
      return { ...(meta as Omit<Termino, "id" | "cuerpo">), id: f.replace(/\.mdx$/, ""), cuerpo };
    })
    .sort((a, b) => a.termino.localeCompare(b.termino, "es"));
}

/** Problemas de un término; vacío si todo está bien. */
export function validarTermino(t: Termino, vias: string[]): string[] {
  const errores: string[] = [];
  if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(t.id)) errores.push(`${t.id}: el nombre del archivo debe ser un slug sin tildes`);
  if (!t.termino?.trim()) errores.push(`${t.id}: falta termino`);
  if (!t.breve?.trim()) errores.push(`${t.id}: falta breve`);
  if (!Array.isArray(t.formas) || t.formas.length === 0) errores.push(`${t.id}: falta formas`);
  if (!ESTADOS_EDITORIALES.includes(t.estado_editorial)) errores.push(`${t.id}: estado_editorial desconocido`);
  if (typeof t.generado_con_ia !== "boolean") errores.push(`${t.id}: generado_con_ia debe ser true o false`);
  if (t.estado_editorial !== "borrador" && (t.revisores?.length ?? 0) === 0) {
    errores.push(`${t.id}: un término ${t.estado_editorial} necesita al menos un revisor`);
  }
  for (const v of t.vias ?? []) if (!vias.includes(v)) errores.push(`${t.id}: vía desconocida ${v}`);
  return errores;
}

/** Formas repetidas entre términos (cada forma debe llevar a un solo término). */
export function formasRepetidas(terminos: Termino[]): string[] {
  const vistas = new Map<string, string>();
  const repetidas: string[] = [];
  for (const t of terminos) {
    for (const f of t.formas) {
      const clave = f.toLocaleLowerCase("es");
      if (vistas.has(clave)) repetidas.push(`${f} (${vistas.get(clave)} y ${t.id})`);
      vistas.set(clave, t.id);
    }
  }
  return repetidas;
}

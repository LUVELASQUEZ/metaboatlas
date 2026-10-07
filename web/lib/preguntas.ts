// Preguntas de autoevaluación (content/preguntas/<slug>.json, sección 10 de docs/MANUAL.md).
// Se corrigen en el navegador y no se guarda ningún resultado.
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { DIR_CONTENIDO, ESTADOS_EDITORIALES } from "@/lib/contenido";
import { NIVELES, type Nivel } from "@/lib/niveles";
import type { Via } from "@/lib/tipos/via";

interface Base {
  id: string;
  nivel: Nivel;
  enunciado: string;
  explicacion: string;
}

export interface OpcionMultiple extends Base {
  tipo: "opcion_multiple";
  opciones: string[];
  correcta: number;
  /** Datos con que las pruebas comprueban la respuesta contra la curaduría. */
  verifica?: Record<string, unknown>;
}

/** Ordenar pasos de la vía: el orden correcto es el de la curaduría. */
export interface OrdenarPasos extends Base {
  tipo: "ordenar_pasos";
  pasos: string[];
}

export type Pregunta = OpcionMultiple | OrdenarPasos;

export interface Autoevaluacion {
  via: string;
  estado_editorial: (typeof ESTADOS_EDITORIALES)[number];
  generado_con_ia: boolean;
  revisores: string[];
  actualizado: string;
  preguntas: Pregunta[];
}

export function leerPreguntas(slug: string, raiz = DIR_CONTENIDO): Autoevaluacion | null {
  const archivo = path.join(raiz, "preguntas", `${slug}.json`);
  if (!existsSync(archivo)) return null;
  return JSON.parse(readFileSync(archivo, "utf8")) as Autoevaluacion;
}

/** Problemas de las preguntas frente a la vía curada; vacío si todo está bien. */
export function validarPreguntas(a: Autoevaluacion, via: Via): string[] {
  const errores: string[] = [];
  if (a.via !== via.id) errores.push(`via es ${a.via}, se esperaba ${via.id}`);
  if (!ESTADOS_EDITORIALES.includes(a.estado_editorial)) errores.push("estado_editorial desconocido");
  if (typeof a.generado_con_ia !== "boolean") errores.push("generado_con_ia debe ser true o false");
  if (a.estado_editorial !== "borrador" && (a.revisores?.length ?? 0) === 0) {
    errores.push(`unas preguntas ${a.estado_editorial} necesitan al menos un revisor`);
  }
  const ids = new Set<string>();
  for (const p of a.preguntas) {
    if (ids.has(p.id)) errores.push(`id repetido: ${p.id}`);
    ids.add(p.id);
    if (!NIVELES.includes(p.nivel)) errores.push(`${p.id}: nivel desconocido ${p.nivel}`);
    if (!p.enunciado?.trim() || !p.explicacion?.trim()) errores.push(`${p.id}: falta enunciado o explicación`);
    if (p.tipo === "opcion_multiple") {
      if (p.opciones.length < 2) errores.push(`${p.id}: necesita al menos dos opciones`);
      if (!Number.isInteger(p.correcta) || p.correcta < 0 || p.correcta >= p.opciones.length) {
        errores.push(`${p.id}: correcta fuera de rango`);
      }
    } else if (p.tipo === "ordenar_pasos") {
      if (p.pasos.length < 2) errores.push(`${p.id}: necesita al menos dos pasos`);
      for (const id of p.pasos) if (!via.pasos.some((x) => x.id === id)) errores.push(`${p.id}: paso inexistente ${id}`);
    } else {
      errores.push(`${(p as Base).id}: tipo desconocido`);
    }
  }
  for (const nivel of NIVELES) {
    if (!a.preguntas.some((p) => p.nivel === nivel)) errores.push(`no hay preguntas de nivel ${nivel}`);
  }
  return errores;
}

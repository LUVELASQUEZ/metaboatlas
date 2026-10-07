// Algoritmo de cobertura (sección 5 de docs/MANUAL.md), gemelo de
// pipeline/metabo/coverage/algorithm.py. Los dos pasan los casos de
// schema/casos/cobertura.json; si cambia una regla, se cambia ahí primero.
//
// Para un paso P y un organismo O, en este orden:
// 1. P espontáneo -> `espontaneo` (cuenta como presente).
// 2. Proteína revisada (Swiss-Prot) de O con alguna reacción Rhea de P -> `alta`.
// 3. Proteína no revisada (TrEMBL) de O con alguna reacción Rhea de P -> `media`.
// 4. Proteína de O con alguno de los números EC de P -> `baja` (probable; no suma).
// 5. Nada -> `sin_anotacion`. Nunca "ausente".
//
// Las reacciones Rhea de las proteínas se comparan por su reacción maestra y los
// números EC, completos y exactos.

import type { Cobertura, EstadoPaso } from "@/lib/tipos/cobertura";

export type Estado = EstadoPaso["estado"];
export type Clase = Cobertura["clase"];

export const PRESENTES: ReadonlySet<Estado> = new Set(["espontaneo", "alta", "media"]);
export const ADVERTENCIA_COMPLEJO = "complejo_verificar_subunidades";

export interface Step {
  id: string;
  reacciones: readonly string[];
  ec: readonly string[];
  espontaneo?: boolean;
  complejo?: boolean;
}

export interface Protein {
  accession: string;
  revisada: boolean;
  rhea: readonly string[];
  ec: readonly string[];
}

export interface Thresholds {
  completa: number;
  casi_completa: number;
  parcial: number;
}

export interface StepResult {
  estado: Estado;
  proteinas: string[];
  advertencias?: (typeof ADVERTENCIA_COMPLEJO)[];
}

export interface PathwayResult {
  cobertura: number;
  clase: Clase;
  pasos: Record<string, StepResult>;
}

/** Proteínas de un organismo indexadas por reacción Rhea maestra y por número EC. */
export class ProteomeIndex {
  private readonly byRhea = new Map<string, Protein[]>();
  private readonly byEc = new Map<string, Protein[]>();

  constructor(proteins: Iterable<Protein>, maestras: Readonly<Record<string, string>> = {}) {
    for (const protein of proteins) {
      for (const rid of new Set(protein.rhea.map((r) => maestras[r] ?? r))) {
        push(this.byRhea, rid, protein);
      }
      for (const ec of new Set(protein.ec)) push(this.byEc, ec, protein);
    }
  }

  withRhea(reacciones: readonly string[]): Protein[] {
    return reacciones.flatMap((r) => this.byRhea.get(r) ?? []);
  }

  withEc(ecs: readonly string[]): Protein[] {
    return ecs.flatMap((ec) => this.byEc.get(ec) ?? []);
  }
}

function push<T>(map: Map<string, T[]>, key: string, value: T) {
  const list = map.get(key);
  if (list) list.push(value);
  else map.set(key, [value]);
}

function accessions(proteins: Protein[]): string[] {
  return [...new Set(proteins.map((p) => p.accession))].sort();
}

/** Estado de evidencia de un paso en un organismo (reglas 1 a 5). */
export function stepStatus(step: Step, index: ProteomeIndex): StepResult {
  if (step.espontaneo) return { estado: "espontaneo", proteinas: [] };
  const byRhea = index.withRhea(step.reacciones);
  const reviewed = byRhea.filter((p) => p.revisada);
  let estado: Estado;
  let proteins: Protein[];
  if (reviewed.length > 0) [estado, proteins] = ["alta", reviewed];
  else if (byRhea.length > 0) [estado, proteins] = ["media", byRhea];
  else {
    const byEc = index.withEc(step.ec);
    if (byEc.length === 0) return { estado: "sin_anotacion", proteinas: [] };
    [estado, proteins] = ["baja", byEc];
  }
  const result: StepResult = { estado, proteinas: accessions(proteins) };
  if (step.complejo) result.advertencias = [ADVERTENCIA_COMPLEJO];
  return result;
}

/** Clase de cobertura. Compara con enteros para que 4/5 sea exactamente 80 %. */
export function classify(presentes: number, total: number, umbrales: Thresholds): Clase {
  if (total <= 0) throw new Error("Una vía sin pasos no tiene cobertura.");
  const scaled = presentes * 100;
  if (scaled >= umbrales.completa * total) return "completa";
  if (scaled >= umbrales.casi_completa * total) return "casi_completa";
  if (scaled >= umbrales.parcial * total) return "parcial";
  return "no_detectada";
}

/** Redondeo a un decimal como el `round` de Python (mitad al par). */
function round1(value: number): number {
  const scaled = value * 10;
  const floor = Math.floor(scaled);
  const diff = scaled - floor;
  const rounded = diff > 0.5 || (diff === 0.5 && floor % 2 !== 0) ? floor + 1 : floor;
  return rounded / 10;
}

/** Estado de cada paso, porcentaje de pasos presentes o espontáneos y clase. */
export function pathwayCoverage(
  steps: readonly Step[],
  index: ProteomeIndex,
  umbrales: Thresholds,
): PathwayResult {
  if (steps.length === 0) throw new Error("Una vía sin pasos no tiene cobertura.");
  const pasos: Record<string, StepResult> = {};
  for (const step of steps) pasos[step.id] = stepStatus(step, index);
  const presentes = Object.values(pasos).filter((r) => PRESENTES.has(r.estado)).length;
  return {
    cobertura: round1((presentes * 100) / steps.length),
    clase: classify(presentes, steps.length, umbrales),
    pasos,
  };
}

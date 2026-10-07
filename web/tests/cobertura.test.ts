// Los casos compartidos con la implementación Python (pipeline/tests/test_coverage.py).
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import {
  type Protein,
  type Step,
  type Thresholds,
  classify,
  pathwayCoverage,
  ProteomeIndex,
} from "@/lib/cobertura";

interface Case {
  nombre: string;
  umbrales?: Thresholds;
  pasos: Step[];
  maestras?: Record<string, string>;
  proteinas: Protein[];
  esperado: { cobertura: number; clase: string; pasos: Record<string, unknown> };
}

const spec = JSON.parse(
  readFileSync(new URL("../../schema/casos/cobertura.json", import.meta.url), "utf8"),
) as { umbrales: Thresholds; casos: Case[] };

describe("casos de schema/casos/cobertura.json", () => {
  it.each(spec.casos.map((c) => [c.nombre, c] as const))("%s", (_, caso) => {
    const index = new ProteomeIndex(caso.proteinas, caso.maestras);
    const result = pathwayCoverage(caso.pasos, index, caso.umbrales ?? spec.umbrales);
    expect(result).toEqual(caso.esperado);
  });
});

describe("classify", () => {
  const umbrales = { completa: 100, casi_completa: 80, parcial: 30 };

  it("4 de 5 es exactamente 80 %", () => {
    expect(classify(4, 5, umbrales)).toBe("casi_completa");
  });

  it("una vía sin pasos no tiene cobertura", () => {
    expect(() => classify(0, 0, umbrales)).toThrow();
    expect(() => pathwayCoverage([], new ProteomeIndex([]), umbrales)).toThrow();
  });
});

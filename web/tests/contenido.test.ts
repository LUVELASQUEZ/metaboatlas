// Contenido didáctico de content/vias/ frente a la curaduría de curation/vias/. No
// necesita el paquete de datos: la curaduría ya trae los pasos y su `energia`.
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { parse } from "yaml";
import { balanceEnergetico } from "@/lib/balance";
import { compilarContenido, type ContenidoVia, leerContenidoVia, validarContenido } from "@/lib/contenido";
import type { Via } from "@/lib/tipos/via";

const raiz = path.join(__dirname, "..", "..");
const contenidoDir = path.join(raiz, "content");
const curada = (slug: string) =>
  parse(readFileSync(path.join(raiz, "curation", "vias", `${slug}.yaml`), "utf8")) as Via & {
    modulos: { id: string; pasos: string[] }[];
  };
const slugs = readdirSync(path.join(contenidoDir, "vias"))
  .filter((f) => f.endsWith(".mdx"))
  .map((f) => f.replace(/\.mdx$/, ""));

/** Pasos que el MDX pide contar dos veces en <BalanceEnergetico duplicados={[...]} />. */
function duplicadosDelMdx(cuerpo: string): string[] {
  const m = /<BalanceEnergetico\s+duplicados=\{(\[[^\]]*\])\}/.exec(cuerpo);
  return m ? (JSON.parse(m[1]!) as string[]) : [];
}

describe.each(slugs)("content/vias/%s.mdx", (slug) => {
  const contenido = leerContenidoVia(slug, contenidoDir)!;
  const via = curada(slug);

  it("coincide con la vía curada: un texto por paso y los tres niveles", () => {
    expect(validarContenido(contenido, via)).toEqual([]);
  });

  it("se compila y muestra un bloque por nivel", async () => {
    const Contenido = await compilarContenido(contenido.cuerpo);
    const html = renderToStaticMarkup(
      createElement(Contenido, {
        components: {
          Nivel: ({ nivel, children }: { nivel: string; children: React.ReactNode }) =>
            createElement("section", { "data-nivel": nivel }, children),
          RefPendiente: () => null,
          BalanceEnergetico: () => null,
        },
      }),
    );
    for (const nivel of ["basico", "intermedio", "avanzado"]) {
      expect(html).toContain(`data-nivel="${nivel}"`);
    }
  });
});

describe("balance de la glucólisis", () => {
  const contenido = leerContenidoVia("glucolisis", contenidoDir)!;
  const via = curada("glucolisis");
  const duplicados = duplicadosDelMdx(contenido.cuerpo);

  it("cuenta dos veces justo la fase de las triosas (módulo m2)", () => {
    expect(duplicados).toEqual(via.modulos.find((m) => m.id === "m2")!.pasos);
  });

  // Lo que afirma el texto: se gastan 2 ATP, se forman 4 (neto +2) y se forman 2 NADH.
  it("da lo que dice el texto: +2 ATP y +2 NADH por glucosa", () => {
    expect(balanceEnergetico(via.pasos, duplicados)).toEqual([
      { molecula: "ATP", consumidas: 2, producidas: 4, neto: 2 },
      { molecula: "NADH", consumidas: 0, producidas: 2, neto: 2 },
    ]);
  });

  it("rechaza pasos inexistentes", () => {
    expect(() => balanceEnergetico(via.pasos, ["p99"])).toThrow("p99");
  });
});

describe("validación del contenido", () => {
  const via = {
    id: "via:prueba",
    pasos: [{ id: "p01" }, { id: "p02" }],
  } as unknown as Via;
  const base = (): ContenidoVia => ({
    meta: {
      via: "via:prueba",
      estado_editorial: "borrador",
      generado_con_ia: true,
      revisores: [],
      actualizado: "2026-10-07",
      pasos: { p01: "uno", p02: "dos" },
    },
    cuerpo: '<Nivel nivel="basico">a</Nivel><Nivel nivel="intermedio">b</Nivel><Nivel nivel="avanzado">c</Nivel>',
  });

  it("acepta un contenido completo", () => {
    expect(validarContenido(base(), via)).toEqual([]);
  });

  it("detecta pasos sin texto, pasos que no existen y niveles faltantes", () => {
    const c = base();
    c.meta.pasos = { p01: "uno", p03: "tres" };
    c.cuerpo = '<Nivel nivel="basico">a</Nivel>';
    expect(validarContenido(c, via)).toEqual([
      "falta el texto del paso p02",
      "texto para un paso que no existe: p03",
      "falta el nivel intermedio",
      "falta el nivel avanzado",
    ]);
  });

  it("no deja marcar como revisado un texto sin revisores", () => {
    const c = base();
    c.meta.estado_editorial = "revisado";
    expect(validarContenido(c, via)).toEqual(["un contenido revisado necesita al menos un revisor"]);
  });
});

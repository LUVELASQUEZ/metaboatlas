// Glosario, enlaces automáticos a sus términos y preguntas de autoevaluación, frente a
// la curaduría (curation/). No necesita el paquete de datos.
import { readFileSync } from "node:fs";
import path from "node:path";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { parse } from "yaml";
import { desordenar } from "@/components/contenido/Autoevaluacion";
import { balanceEnergetico } from "@/lib/balance";
import { compilarContenido, leerContenidoVia } from "@/lib/contenido";
import { formasRepetidas, leerGlosario, validarTermino } from "@/lib/glosario";
import { leerPreguntas, type OpcionMultiple, validarPreguntas } from "@/lib/preguntas";
import type { Via } from "@/lib/tipos/via";

const raiz = path.join(__dirname, "..", "..");
const contenidoDir = path.join(raiz, "content");
const leerYaml = (relativo: string) => parse(readFileSync(path.join(raiz, relativo), "utf8"));
const via = leerYaml("curation/vias/glucolisis.yaml") as Via & { modulos: { id: string; pasos: string[] }[] };
const mapa = JSON.parse(readFileSync(path.join(raiz, "curation/mapas/glucolisis.json"), "utf8")) as {
  pasos: { paso: string; hacia: string[] }[];
};
const glosario = leerGlosario(contenidoDir);

/** HTML del MDX con los enlaces del glosario; cada enlace queda como <a data-termino>. */
async function html(cuerpo: string): Promise<string> {
  const Contenido = await compilarContenido(cuerpo, glosario);
  return renderToStaticMarkup(
    createElement(Contenido, {
      components: {
        Nivel: ({ nivel, children }: { nivel: string; children: React.ReactNode }) =>
          createElement("section", { "data-nivel": nivel }, children),
        TerminoGlosario: ({ id, children }: { id: string; children: React.ReactNode }) =>
          createElement("a", { "data-termino": id }, children),
        RefPendiente: () => null,
        BalanceEnergetico: () => null,
        Autoevaluacion: () => null,
      },
    }),
  );
}
const enlaces = (s: string) => [...s.matchAll(/data-termino="([^"]+)">([^<]+)</g)].map((m) => `${m[1]}:${m[2]}`);

describe("glosario", () => {
  it("cada término es válido y apunta a vías curadas", () => {
    expect(glosario.length).toBeGreaterThan(0);
    expect(glosario.flatMap((t) => validarTermino(t, [via.id]))).toEqual([]);
  });

  it("cada forma lleva a un solo término", () => {
    expect(formasRepetidas(glosario)).toEqual([]);
  });
});

describe("enlaces al glosario", () => {
  it("enlaza solo la primera aparición, como palabra completa y fuera de los títulos", async () => {
    const salida = await html("## La cinasa\n\nUna cinasa usa ATP. La hexocinasa es otra cinasa y gasta ATP.\n");
    expect(enlaces(salida)).toEqual(["cinasa:cinasa", "atp:ATP"]);
  });

  it("distingue NAD+ de NADH y prefiere la forma más larga", async () => {
    const salida = await html("El NAD+ se reduce a NADH. Las triosas fosfato se igualan.\n");
    expect(enlaces(salida)).toEqual(["nad:NAD+", "triosa-fosfato:triosas fosfato"]);
  });

  it("cada nivel es un texto aparte", async () => {
    const salida = await html(
      '<Nivel nivel="basico">\n\nSe forma ATP.\n\n</Nivel>\n\n<Nivel nivel="intermedio">\n\nSe gasta ATP.\n\n</Nivel>\n\nFuera, ATP.\n',
    );
    expect(enlaces(salida)).toEqual(["atp:ATP", "atp:ATP", "atp:ATP"]);
  });

  it("la glucólisis enlaza términos en los tres niveles", async () => {
    const salida = await html(leerContenidoVia("glucolisis", contenidoDir)!.cuerpo);
    for (const nivel of ["basico", "intermedio", "avanzado"]) {
      const bloque = salida.split(`data-nivel="${nivel}"`)[1]!.split("</section>")[0]!;
      expect(enlaces(bloque).length, nivel).toBeGreaterThan(0);
    }
  });
});

describe("preguntas de la glucólisis", () => {
  const a = leerPreguntas("glucolisis", contenidoDir)!;
  const opcion = (id: string) => a.preguntas.find((p) => p.id === id) as OpcionMultiple;
  const verificadas = a.preguntas.filter((p): p is OpcionMultiple => p.tipo === "opcion_multiple" && !!p.verifica);
  const duplicados = via.modulos.find((m) => m.id === "m2")!.pasos;

  it("son válidas frente a la vía curada", () => {
    expect(validarPreguntas(a, via)).toEqual([]);
  });

  it("las de balance coinciden con la energía curada", () => {
    const neto = Object.fromEntries(balanceEnergetico(via.pasos, duplicados).map((f) => [f.molecula, f.neto]));
    const deBalance = verificadas.filter((p) => "molecula" in p.verifica!);
    expect(deBalance.length).toBeGreaterThan(0);
    for (const p of deBalance) {
      const v = p.verifica as { molecula: string; glucosas: number; valores: number[] };
      expect(v.valores, p.id).toHaveLength(p.opciones.length);
      expect(v.valores.filter((x) => x === neto[v.molecula]! * v.glucosas), p.id).toHaveLength(1);
      expect(v.valores[p.correcta], p.id).toBe(neto[v.molecula]! * v.glucosas);
    }
  });

  it("el producto final es el que deja la última flecha del mapa", () => {
    const p = opcion("producto-final");
    const ultimo = [...via.pasos].sort((x, y) => y.orden - x.orden)[0]!;
    const hacia = mapa.pasos.find((f) => f.paso === ultimo.id)!.hacia;
    expect(hacia).toContain((p.verifica as { compuesto_final: string }).compuesto_final);
  });

  it("el paso que forma NADH es el único de las opciones con NADH", () => {
    const p = opcion("paso-nadh");
    const pasos = (p.verifica as { pasos: string[] }).pasos;
    const conNadh = pasos.map((id) => (via.pasos.find((x) => x.id === id)!.energia?.NADH ?? 0) > 0);
    expect(conNadh).toEqual(pasos.map((_, i) => i === p.correcta));
  });

  it("el paso regulado es el único de las opciones marcado como regulado", () => {
    const p = opcion("control-principal");
    const pasos = (p.verifica as { paso_regulado: string[] }).paso_regulado;
    expect(pasos.map((id) => via.pasos.find((x) => x.id === id)!.regulacion)).toEqual(pasos.map((_, i) => i === p.correcta));
  });

  it("los EC del paso 8 son los de la curaduría", () => {
    const v = opcion("dos-mutasas").verifica as { ec_del_paso: { paso: string; ec: string[] } };
    expect(via.pasos.find((x) => x.id === v.ec_del_paso.paso)!.ec).toEqual(v.ec_del_paso.ec);
  });

  it("ordenar pasos usa el orden de la curaduría", () => {
    for (const p of a.preguntas) {
      if (p.tipo !== "ordenar_pasos") continue;
      const ordenes = p.pasos.map((id) => via.pasos.find((x) => x.id === id)!.orden);
      expect(ordenes, p.id).toEqual([...ordenes].sort((x, y) => x - y));
    }
  });
});

describe("desordenar", () => {
  it("es determinista y nunca deja el orden correcto", () => {
    const ids = ["p01", "p02", "p03", "p04", "p05"];
    expect(desordenar(ids, "q")).toEqual(desordenar(ids, "q"));
    expect(desordenar(ids, "q")).not.toEqual(ids);
    expect([...desordenar(ids, "q")].sort()).toEqual(ids);
    expect(desordenar(["a", "b"], "x")).toEqual(["b", "a"]);
  });
});

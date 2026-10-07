// La página de la glucólisis con el paquete de datos real (public/datos/). Necesita
// `npm run datos`, que a su vez necesita el paquete del pipeline; sin él se omite.
import { existsSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { Paquete } from "@/lib/datos";
import { leerFuentes } from "@/lib/fuentes";
import { construirVistaVia } from "@/lib/vista-via";

const raiz = path.join(__dirname, "..", "public", "datos");
const hayDatos = existsSync(path.join(raiz, "version.json"));

describe.skipIf(!hayDatos)("glucólisis con datos reales", () => {
  const vista = () =>
    construirVistaVia(
      Paquete.actual(raiz),
      leerFuentes(path.join(__dirname, "..", "..", "sources.yaml")),
      "glucolisis",
    );

  it("dibuja los 10 pasos y ofrece los organismos de la fase 0", () => {
    const v = vista();
    expect(v.mapa?.flechas.map((f) => f.paso).sort()).toEqual(v.pasos.map((p) => p.id).sort());
    expect(v.organismos.map((o) => o.id).sort()).toEqual(
      ["taxon:224308", "taxon:511145", "taxon:559292", "taxon:9606"].sort(),
    );
  });

  // Balance energético de los libros de texto, deducido de las ecuaciones de Rhea y del
  // sentido de cada flecha: dos fosforilaciones gastan ATP, dos lo producen y la
  // gliceraldehído 3-fosfato deshidrogenasa produce NADH.
  it.each([
    ["p01", "consume", "CHEBI:30616"], // hexocinasa: ATP
    ["p03", "consume", "CHEBI:30616"], // fosfofructocinasa: ATP
    ["p06", "produce", "CHEBI:57945"], // GAPDH: NADH
    ["p07", "produce", "CHEBI:30616"], // fosfoglicerato cinasa: ATP
    ["p10", "produce", "CHEBI:30616"], // piruvato cinasa: ATP
  ] as const)("%s %s %s", (paso, lado, compuesto) => {
    expect(vista().pasos.find((p) => p.id === paso)![lado]).toContain(compuesto);
  });

  it("muestra los nombres de lectura de Rhea", () => {
    const v = vista();
    expect(v.compuestos["CHEBI:57540"]!.nombre).toBe("NAD(+)");
    expect(v.compuestos["CHEBI:57642"]!.nombre).toBe("dihydroxyacetone phosphate");
  });
});

// Vista de una vía y elementos del mapa con un paquete ficticio. Sus IDs, nombres y
// ecuaciones son ficticios: prueban la lógica, no son datos.
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { beforeAll, describe, expect, it } from "vitest";
import { Paquete } from "@/lib/datos";
import { elementosMapa, textoCofactores, textoRotulo } from "@/lib/elementos-mapa";
import { enlace, type Fuentes, leerFuentes, plantilla } from "@/lib/fuentes";
import type { Cobertura } from "@/lib/tipos/cobertura";
import type { Reaccion } from "@/lib/tipos/reaccion";
import { construirVistaVia, nombresEnEcuacion, type VistaVia } from "@/lib/vista-via";

const procedencia = (fuente: string, id: string) => [
  { fuente, id, version: "1", fecha_descarga: "2026-10-07" },
];

function reaccion(id: string, ecuacion: string, izquierda: string[], derecha: string[]): Reaccion {
  return {
    id,
    ecuacion,
    participantes: [
      ...izquierda.map((c) => ({ compuesto: c, lado: "izquierda" as const, estequiometria: 1 })),
      ...derecha.map((c) => ({ compuesto: c, lado: "derecha" as const, estequiometria: 1 })),
    ],
    direcciones: {
      izquierda_a_derecha: "RHEA:1001",
      derecha_a_izquierda: "RHEA:1002",
      bidireccional: "RHEA:1003",
    },
    reversible: null,
    es_transporte: false,
    ec: [],
    delta_g: null,
    xrefs: [],
    procedencia: procedencia("rhea", id.slice(5)),
  } as unknown as Reaccion;
}

const compuesto = (n: string, nombre: string, cofactor = false) => ({
  id: `CHEBI:${n}`,
  nombre: { es: null, en: nombre },
  definicion: null,
  sinonimos: [],
  formula: "C6H12O6",
  carga: 0,
  masa_monoisotopica: 180.1,
  smiles: null,
  inchi: null,
  inchikey: null,
  clase: cofactor ? "cofactor" : "carbohidrato",
  es_cofactor: cofactor,
  xrefs: [],
  procedencia: procedencia("chebi", n),
});

// Paso 1: 1 + moneda(3) = 2 + moneda gastada(4). Paso 2, dibujado al revés de su
// reacción de Rhea (5 + moneda gastada(4) = 2 + moneda(3)): en la vía, 2 -> 5 gasta la
// moneda (3) y deja la moneda gastada (4).
const ARCHIVOS: Record<string, unknown> = {
  "vias/prueba.json": {
    id: "via:prueba",
    nombre: { es: "Vía de prueba", en: "Test pathway" },
    modulos: [{ id: "m1", nombre: "Módulo de prueba", pasos: ["p01", "p02"] }],
    pasos: [
      { id: "p01", orden: 1, titulo: "Paso uno", reacciones: ["RHEA:1000"], ec: ["EC:9.9.9.1"], espontaneo: false, regulacion: true },
      { id: "p02", orden: 2, titulo: "Paso dos", reacciones: ["RHEA:2000"], ec: ["EC:9.9.9.2"], espontaneo: false, regulacion: false },
    ],
    fuentes: { rhea: "1" },
  },
  "mapas/prueba.json": {
    via: "via:prueba",
    lienzo: { ancho: 300, alto: 400 },
    compuestos: [
      { compuesto: "CHEBI:1", x: 100, y: 50 },
      { compuesto: "CHEBI:2", x: 100, y: 200, etiqueta: "derecha" },
      { compuesto: "CHEBI:5", x: 100, y: 350 },
    ],
    pasos: [
      { paso: "p01", desde: ["CHEBI:1"], hacia: ["CHEBI:2"], rotulo: { x: 100, y: 125 }, cofactores: "derecha" },
      { paso: "p02", desde: ["CHEBI:2"], hacia: ["CHEBI:5"], rotulo: { x: 100, y: 275 }, cofactores: "izquierda" },
    ],
    modulos: [{ modulo: "m1", x: 10, y: 10, ancho: 280, alto: 380 }],
    portales: [],
  },
  "reacciones/RHEA_1000.json": reaccion(
    "RHEA:1000",
    "sugar + coin = sugar phosphate + 2 spent coin",
    ["CHEBI:1", "CHEBI:3"],
    ["CHEBI:2", "CHEBI:4"],
  ),
  "reacciones/RHEA_2000.json": reaccion(
    "RHEA:2000",
    "other sugar + spent coin = sugar phosphate + coin",
    ["CHEBI:5", "CHEBI:4"],
    ["CHEBI:2", "CHEBI:3"],
  ),
  "compuestos/CHEBI_1.json": compuesto("1", "azúcar(0)"),
  "compuestos/CHEBI_2.json": compuesto("2", "azúcar fosfato(2−)"),
  "compuestos/CHEBI_3.json": compuesto("3", "moneda(4−)", true),
  "compuestos/CHEBI_4.json": compuesto("4", "moneda gastada(3−)", true),
  "compuestos/CHEBI_5.json": compuesto("5", "otro azúcar"),
  "enzimas/EC_9.9.9.1.json": { id: "EC:9.9.9.1", nombre: { es: null, en: "enzima uno" }, proteinas: [], procedencia: procedencia("enzyme", "9.9.9.1") },
  "enzimas/EC_9.9.9.2.json": { id: "EC:9.9.9.2", nombre: { es: null, en: "enzima dos" }, proteinas: [], procedencia: procedencia("enzyme", "9.9.9.2") },
  "organismos/13.json": { id: "taxon:13", nombre_cientifico: "Bacteria ficticia", dominio: "bacteria", procedencia: [] },
  "organismos/14.json": { id: "taxon:14", nombre_cientifico: "Sin cobertura", dominio: "bacteria", procedencia: [] },
  "cobertura/prueba/13.json": { via: "via:prueba", taxon: "taxon:13", pasos: {}, fuentes: {} },
};

const FUENTES: Fuentes = {
  rhea: {
    clave: "rhea", nombre: "Rhea", uso: "redistribuir", estado: "verificada", url: null,
    licencia: "CC BY 4.0", licencia_url: null, verificada: "2026-10-07", condicion: null,
    plantillas: { reaccion: "https://rhea.example/rhea/{id}" }, cita_recomendada: null, doi_cita: null,
  },
  kegg: {
    clave: "kegg", nombre: "KEGG", uso: "solo_enlace", estado: "pendiente de verificar", url: null,
    licencia: "", licencia_url: null, verificada: null, condicion: null,
    plantillas: { enzima: "https://kegg.example/entry/{id}" }, cita_recomendada: null, doi_cita: null,
  },
};

let vista: VistaVia;

beforeAll(() => {
  const dir = mkdtempSync(path.join(tmpdir(), "metabo-"));
  for (const [archivo, contenido] of Object.entries(ARCHIVOS)) {
    mkdirSync(path.dirname(path.join(dir, archivo)), { recursive: true });
    writeFileSync(path.join(dir, archivo), JSON.stringify(contenido));
  }
  vista = construirVistaVia(new Paquete(dir, "2026.10"), FUENTES, "prueba");
});

describe("nombresEnEcuacion", () => {
  it("toma el nombre de cada participante de la ecuación, sin coeficiente", () => {
    const nombres = nombresEnEcuacion(ARCHIVOS["reacciones/RHEA_1000.json"] as Reaccion);
    expect(Object.fromEntries(nombres)).toEqual({
      "CHEBI:1": "sugar",
      "CHEBI:3": "coin",
      "CHEBI:2": "sugar phosphate",
      "CHEBI:4": "spent coin",
    });
  });

  it("no adivina si los términos no coinciden con los participantes", () => {
    const r = reaccion("RHEA:9", "a + b = c", ["CHEBI:1"], ["CHEBI:2"]);
    expect(nombresEnEcuacion(r).size).toBe(0);
  });
});

describe("construirVistaVia", () => {
  it("usa el nombre de Rhea y conserva el de ChEBI", () => {
    expect(vista.compuestos["CHEBI:2"]).toMatchObject({
      nombre: "sugar phosphate",
      nombreChebi: "azúcar fosfato(2−)",
    });
    // Sin nombre en ninguna ecuación: el de ChEBI.
    expect(vista.compuestos["CHEBI:5"]!.nombre).toBe("other sugar");
  });

  it("orienta los cofactores en el sentido de la flecha, no de la reacción", () => {
    const [p01, p02] = vista.pasos;
    expect([p01!.consume, p01!.produce]).toEqual([["CHEBI:3"], ["CHEBI:4"]]);
    expect([p02!.consume, p02!.produce]).toEqual([["CHEBI:3"], ["CHEBI:4"]]);
  });

  it("solo ofrece organismos con cobertura calculada", () => {
    expect(vista.organismos.map((o) => o.id)).toEqual(["taxon:13"]);
  });

  it("enlaza solo fuentes verificadas", () => {
    expect(vista.reacciones["RHEA:1000"]!.origen[0]!.url).toBe("https://rhea.example/rhea/1000");
    expect(vista.enzimas["EC:9.9.9.1"]!.origen[0]!.url).toBeNull();
  });
});

describe("elementos del mapa", () => {
  it("sin organismo, los rótulos son neutros", () => {
    const rotulos = elementosMapa(vista, null).filter((e) => e.data.tipo === "rotulo");
    expect(rotulos.map((r) => r.data.estado)).toEqual(["neutro", "neutro"]);
  });

  it("con organismo, cada rótulo toma su estado; sin anotación lleva un signo", () => {
    const cobertura = {
      pasos: { p01: { estado: "alta", proteinas: ["UNIPROT:Z9Z991"] }, p02: { estado: "sin_anotacion", proteinas: [] } },
    } as unknown as Cobertura;
    const rotulos = elementosMapa(vista, cobertura).filter((e) => e.data.tipo === "rotulo");
    expect(rotulos.map((r) => r.data.estado)).toEqual(["alta", "sin_anotacion"]);
    expect(rotulos[1]!.data.etiqueta).toBe("2. enzima dos\nEC 9.9.9.2 (?)");
  });

  it("marca los pasos regulados con un signo además del borde", () => {
    expect(textoRotulo(vista, "p01", "alta")).toBe("1. enzima uno ◆\nEC 9.9.9.1");
  });

  it("escribe los cofactores junto a la flecha", () => {
    expect(textoCofactores(vista, "p01")).toBe("coin → spent coin");
    expect(textoCofactores(vista, "p02")).toBe("coin → spent coin");
  });

  it("cada rótulo tiene su propia posición (Cytoscape no debe compartir objetos)", () => {
    const elementos = elementosMapa(vista, null);
    const rotulo = elementos.find((e) => e.data.id === "paso:p01")!;
    const cofactores = elementos.find((e) => e.data.id === "cofactores:p01")!;
    expect(rotulo.position).not.toBe(cofactores.position);
  });

  it("una flecha por compuesto de origen y de destino", () => {
    const aristas = elementosMapa(vista, null).filter((e) => e.group === "edges");
    expect(aristas.map((a) => a.data.id)).toEqual([
      "p01:CHEBI:1:entra",
      "p01:CHEBI:2:sale",
      "p02:CHEBI:2:entra",
      "p02:CHEBI:5:sale",
    ]);
  });
});

describe("sources.yaml", () => {
  const fuentes = leerFuentes(path.join(__dirname, "..", "..", "sources.yaml"));

  it("las fuentes de solo enlace sin verificar no generan enlaces", () => {
    expect(fuentes.kegg?.uso).toBe("solo_enlace");
    expect(enlace(fuentes, "kegg", "enzima", "2.7.1.1")).toBeNull();
  });

  it("las fuentes de la fase 0 tienen plantilla de enlace", () => {
    expect(plantilla(fuentes, "uniprot", "proteina")).toContain("{id}");
    expect(enlace(fuentes, "chebi", "compuesto", "15361")).toContain("15361");
  });
});

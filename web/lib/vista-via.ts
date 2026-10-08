// Arma, al construir el sitio, todo lo que la página de una vía necesita en el
// navegador: pasos, nombres para mostrar, ecuaciones, enlaces y el dibujo del mapa.
// Lo que depende del organismo (cobertura, proteínas) se descarga bajo demanda.
import type { Paquete } from "@/lib/datos";
import { enlace, plantilla, type Fuentes } from "@/lib/fuentes";
import { nativo } from "@/lib/rutas";
import type { Compuesto } from "@/lib/tipos/compuesto";
import type { Reaccion } from "@/lib/tipos/reaccion";

type Lado = "izquierda" | "derecha" | "arriba" | "abajo";

export interface Origen {
  fuente: string;
  nombreFuente: string;
  id: string;
  version: string;
  fecha: string;
  url: string | null;
}

export interface CompuestoVista {
  id: string;
  /** Nombre en español si lo hay; si no, el de lectura en inglés (`nombreEn`). */
  nombre: string;
  /** Idioma de `nombre`, para el atributo `lang`. */
  idioma: "es" | "en";
  /** Nombre con que Rhea escribe el compuesto en sus ecuaciones, o el de ChEBI. */
  nombreEn: string;
  nombreChebi: string;
  definicion: string | null;
  formula: string | null;
  carga: number | null;
  masa: number | null;
  clase: Compuesto["clase"];
  esCofactor: boolean;
  origen: Origen[];
}

export interface ReaccionVista {
  id: string;
  ecuacion: string;
  origen: Origen[];
}

export interface EnzimaVista {
  id: string;
  /** Nombre en español si lo hay; si no, el aceptado por ENZYME. */
  nombre: string;
  idioma: "es" | "en";
  /** Nombre aceptado por ENZYME, en inglés. */
  nombreEn: string;
  origen: Origen[];
}

export interface PasoVista {
  id: string;
  orden: number;
  titulo: string;
  modulo: string | null;
  regulacion: boolean;
  espontaneo: boolean;
  reacciones: string[];
  enzimas: string[];
  /** Cofactores en el sentido de la vía (solo si el paso está dibujado). */
  consume: string[];
  produce: string[];
}

export interface MapaVista {
  ancho: number;
  alto: number;
  nodos: { compuesto: string; x: number; y: number; etiqueta: Lado }[];
  flechas: {
    paso: string;
    desde: string[];
    hacia: string[];
    rotulo: { x: number; y: number };
    cofactores: Lado;
  }[];
  regiones: { modulo: string; nombre: string; x: number; y: number; ancho: number; alto: number }[];
}

export interface OrganismoVista {
  id: string;
  nombre: string;
  dominio: string;
  enlace: string | null;
}

export interface VistaVia {
  slug: string;
  version: string;
  modulos: { id: string; nombre: string; resumen: string | null; pasos: string[] }[];
  pasos: PasoVista[];
  compuestos: Record<string, CompuestoVista>;
  reacciones: Record<string, ReaccionVista>;
  enzimas: Record<string, EnzimaVista>;
  mapa: MapaVista | null;
  organismos: OrganismoVista[];
  /** Plantilla de enlace a una proteína de UniProt; `{id}` es la accesión. */
  plantillaProteina: string | null;
}

function origenes(
  fuentes: Fuentes,
  procedencia: { fuente: string; id: string; version: string; fecha_descarga: string }[],
  tipo: string,
): Origen[] {
  return procedencia.map((p) => ({
    fuente: p.fuente,
    nombreFuente: fuentes[p.fuente]?.nombre ?? p.fuente,
    id: p.id,
    version: p.version,
    fecha: p.fecha_descarga,
    // Wikidata enlaza sus elementos (Q…) con una sola plantilla, sea cual sea el tipo.
    url: enlace(fuentes, p.fuente, tipo, p.id) ?? enlace(fuentes, p.fuente, "elemento", p.id),
  }));
}

/**
 * Nombre de cada participante tal como lo escribe la ecuación de Rhea, que usa
 * nombres de lectura ("NAD(+)", "dihydroxyacetone phosphate") en el mismo orden que
 * los participantes. Si el número de términos no coincide, no devuelve nada.
 */
export function nombresEnEcuacion(reaccion: Reaccion): Map<string, string> {
  const nombres = new Map<string, string>();
  const lados = reaccion.ecuacion.split(" = ");
  if (lados.length !== 2) return nombres;
  const terminos = lados.flatMap((lado) => lado.split(" + "));
  if (terminos.length !== reaccion.participantes.length) return nombres;
  reaccion.participantes.forEach((p, i) => {
    const nombre = terminos[i]!.replace(/^(\d+|n|\d+n) /, "").trim();
    if (nombre) nombres.set(p.compuesto, nombre);
  });
  return nombres;
}

export function construirVistaVia(paquete: Paquete, fuentes: Fuentes, slug: string): VistaVia {
  const via = paquete.via(slug);
  const mapa = paquete.mapa(slug);

  const reacciones = new Map<string, Reaccion>();
  for (const paso of via.pasos) {
    for (const rid of paso.reacciones) reacciones.set(rid, paquete.reaccion(rid));
  }

  // Nombres de lectura: el primero que aparece, en el orden de los pasos.
  const nombreRhea = new Map<string, string>();
  for (const reaccion of reacciones.values()) {
    for (const [cid, nombre] of nombresEnEcuacion(reaccion)) {
      if (!nombreRhea.has(cid)) nombreRhea.set(cid, nombre);
    }
  }

  const ids = new Set<string>();
  for (const r of reacciones.values()) for (const p of r.participantes) ids.add(p.compuesto);
  for (const n of mapa?.compuestos ?? []) ids.add(n.compuesto);
  const compuestos: Record<string, CompuestoVista> = {};
  for (const id of [...ids].sort()) {
    const c = paquete.compuesto(id);
    const nombreEn = nombreRhea.get(id) ?? c.nombre.en;
    compuestos[id] = {
      id,
      nombre: c.nombre.es ?? nombreEn,
      idioma: c.nombre.es ? "es" : "en",
      nombreEn,
      nombreChebi: c.nombre.en,
      definicion: c.definicion ?? null,
      formula: c.formula ?? null,
      carga: c.carga ?? null,
      masa: c.masa_monoisotopica ?? null,
      clase: c.clase,
      esCofactor: c.es_cofactor,
      origen: origenes(fuentes, c.procedencia, "compuesto"),
    };
  }

  const enzimas: Record<string, EnzimaVista> = {};
  for (const ec of new Set(via.pasos.flatMap((p) => p.ec))) {
    const e = paquete.enzima(ec);
    enzimas[ec] = {
      id: ec,
      nombre: e.nombre.es ?? e.nombre.en,
      idioma: e.nombre.es ? "es" : "en",
      nombreEn: e.nombre.en,
      origen: origenes(fuentes, e.procedencia, "enzima"),
    };
  }

  const moduloDe = new Map(via.modulos.flatMap((m) => m.pasos.map((p) => [p, m.id] as const)));
  const flechaDe = new Map((mapa?.pasos ?? []).map((f) => [f.paso, f]));
  const pasos: PasoVista[] = via.pasos.map((paso) => {
    const { consume, produce } = cofactoresDelPaso(
      flechaDe.get(paso.id),
      paso.reacciones[0] ? reacciones.get(paso.reacciones[0]) : undefined,
      compuestos,
    );
    return {
      id: paso.id,
      orden: paso.orden,
      titulo: paso.titulo,
      modulo: moduloDe.get(paso.id) ?? null,
      regulacion: paso.regulacion,
      espontaneo: paso.espontaneo,
      reacciones: paso.reacciones,
      enzimas: paso.ec,
      consume,
      produce,
    };
  });

  const nombreModulo = new Map(via.modulos.map((m) => [m.id, m.nombre]));
  const organismos = paquete
    .organismos()
    .filter((o) => paquete.taxonesConCobertura(slug).includes(o.id))
    .map((o) => ({
      id: o.id,
      nombre: o.nombre_cientifico,
      dominio: o.dominio,
      enlace: enlace(fuentes, "ncbi_taxonomy", "organismo", nativo(o.id)),
    }));

  return {
    slug,
    version: paquete.version,
    modulos: via.modulos.map((m) => ({
      id: m.id,
      nombre: m.nombre,
      resumen: m.resumen ?? null,
      pasos: m.pasos,
    })),
    pasos,
    compuestos,
    reacciones: Object.fromEntries(
      [...reacciones.values()].map((r) => [
        r.id,
        { id: r.id, ecuacion: r.ecuacion, origen: origenes(fuentes, r.procedencia, "reaccion") },
      ]),
    ),
    enzimas,
    mapa: mapa && {
      ancho: mapa.lienzo.ancho,
      alto: mapa.lienzo.alto,
      nodos: mapa.compuestos.map((n) => ({
        compuesto: n.compuesto,
        x: n.x,
        y: n.y,
        etiqueta: n.etiqueta ?? "izquierda",
      })),
      flechas: mapa.pasos.map((f) => ({
        paso: f.paso,
        desde: f.desde,
        hacia: f.hacia,
        rotulo: f.rotulo,
        cofactores: f.cofactores,
      })),
      regiones: mapa.modulos.map((m) => ({
        modulo: m.modulo,
        nombre: nombreModulo.get(m.modulo) ?? m.modulo,
        x: m.x,
        y: m.y,
        ancho: m.ancho,
        alto: m.alto,
      })),
    },
    organismos,
    plantillaProteina: plantilla(fuentes, "uniprot", "proteina"),
  };
}

/**
 * Cofactores que el paso consume y produce en el sentido de su flecha. La flecha
 * puede ir al revés de la reacción maestra de Rhea (p. ej. la fosfoglicerato cinasa).
 */
export function cofactoresDelPaso(
  flecha: { desde: string[]; hacia: string[] } | undefined,
  reaccion: Reaccion | undefined,
  compuestos: Record<string, CompuestoVista>,
): { consume: string[]; produce: string[] } {
  if (!flecha || !reaccion) return { consume: [], produce: [] };
  const izquierda = new Set(
    reaccion.participantes.filter((p) => p.lado === "izquierda").map((p) => p.compuesto),
  );
  const alDerecho =
    flecha.desde.some((c) => izquierda.has(c)) || !flecha.hacia.some((c) => izquierda.has(c));
  const cofactores = reaccion.participantes.filter((p) => compuestos[p.compuesto]?.esCofactor);
  const entra = (lado: string) => (lado === "izquierda") === alDerecho;
  return {
    consume: cofactores.filter((p) => entra(p.lado)).map((p) => p.compuesto),
    produce: cofactores.filter((p) => !entra(p.lado)).map((p) => p.compuesto),
  };
}

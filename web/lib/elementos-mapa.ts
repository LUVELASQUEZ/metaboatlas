// Elementos de Cytoscape.js para el mapa de una vía: las posiciones vienen del mapa
// curado y los colores, de la cobertura del organismo elegido (o neutros sin él).
import type { Estado } from "@/lib/cobertura";
import { MARCA_REGULADO } from "@/lib/estilo-evidencia";
import type { Cobertura } from "@/lib/tipos/cobertura";
import type { VistaVia } from "@/lib/vista-via";

export interface Elemento {
  group: "nodes" | "edges";
  data: Record<string, string | number | boolean>;
  position?: { x: number; y: number };
}

const ALINEACION = {
  izquierda: { halign: "left", valign: "center", mx: -8, my: 0 },
  derecha: { halign: "right", valign: "center", mx: 8, my: 0 },
  arriba: { halign: "center", valign: "top", mx: 0, my: -6 },
  abajo: { halign: "center", valign: "bottom", mx: 0, my: 6 },
} as const;

export const idPaso = (paso: string) => `paso:${paso}`;
export const idCofactores = (paso: string) => `cofactores:${paso}`;

/** Texto del rótulo de un paso: enzima y EC, con marcas que no dependen del color. */
export function textoRotulo(
  vista: VistaVia,
  pasoId: string,
  estado: Estado | null,
  conEc = true,
): string {
  const paso = vista.pasos.find((p) => p.id === pasoId)!;
  const enzima = paso.enzimas[0] ? vista.enzimas[paso.enzimas[0]]?.nombre : undefined;
  const titulo = `${paso.orden}. ${enzima ?? paso.titulo}${paso.regulacion ? ` ${MARCA_REGULADO}` : ""}`;
  const ec = !conEc ? "" : paso.enzimas.map((e) => e.replace("EC:", "")).join(", ");
  const duda = estado === "sin_anotacion" ? " (?)" : "";
  return ec ? `${titulo}\nEC ${ec}${duda}` : `${titulo}${duda}`;
}

/** Cofactores de un paso en el sentido de la vía: "ATP → ADP + H(+)". */
export function textoCofactores(vista: VistaVia, pasoId: string): string | null {
  const paso = vista.pasos.find((p) => p.id === pasoId)!;
  if (paso.consume.length === 0 && paso.produce.length === 0) return null;
  const nombres = (ids: string[]) => ids.map((id) => vista.compuestos[id]?.nombre ?? id).join(" + ");
  return `${nombres(paso.consume)} → ${nombres(paso.produce)}`.trim();
}

/** Elementos del mapa. Sin `detallado` (nivel básico) se omiten los EC y los cofactores. */
export function elementosMapa(
  vista: VistaVia,
  cobertura: Cobertura | null,
  detallado = true,
): Elemento[] {
  const mapa = vista.mapa;
  if (!mapa) return [];
  const elementos: Elemento[] = [];
  for (const r of mapa.regiones) {
    elementos.push({
      group: "nodes",
      data: { id: `modulo:${r.modulo}`, tipo: "region", etiqueta: r.nombre, ancho: r.ancho, alto: r.alto },
      position: { x: r.x + r.ancho / 2, y: r.y + r.alto / 2 },
    });
  }
  for (const n of mapa.nodos) {
    const c = vista.compuestos[n.compuesto];
    elementos.push({
      group: "nodes",
      data: {
        id: n.compuesto,
        tipo: "compuesto",
        etiqueta: c?.nombre ?? n.compuesto,
        clase: c?.clase ?? "otro",
        ...ALINEACION[n.etiqueta],
      },
      position: { x: n.x, y: n.y },
    });
  }
  for (const f of mapa.flechas) {
    const paso = vista.pasos.find((p) => p.id === f.paso);
    const estado = cobertura?.pasos[f.paso]?.estado ?? null;
    elementos.push({
      group: "nodes",
      data: {
        id: idPaso(f.paso),
        tipo: "rotulo",
        paso: f.paso,
        etiqueta: textoRotulo(vista, f.paso, estado, detallado),
        estado: estado ?? "neutro",
        regulado: paso?.regulacion ?? false,
      },
      position: { ...f.rotulo },
    });
    const cofactores = detallado ? textoCofactores(vista, f.paso) : null;
    if (cofactores) {
      elementos.push({
        group: "nodes",
        data: {
          id: idCofactores(f.paso),
          tipo: "cofactores",
          paso: f.paso,
          lado: f.cofactores,
          etiqueta: cofactores,
          ...ALINEACION[f.cofactores],
        },
        // Posición provisional: el componente la ajusta al ancho real del rótulo.
        position: { ...f.rotulo },
      });
    }
    for (const c of f.desde) {
      elementos.push({
        group: "edges",
        data: { id: `${f.paso}:${c}:entra`, source: c, target: idPaso(f.paso), tipo: "entra", paso: f.paso },
      });
    }
    for (const c of f.hacia) {
      elementos.push({
        group: "edges",
        data: { id: `${f.paso}:${c}:sale`, source: idPaso(f.paso), target: c, tipo: "sale", paso: f.paso },
      });
    }
  }
  return elementos;
}

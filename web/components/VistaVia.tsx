"use client";

import { parseAsString, useQueryState } from "nuqs";
import { useEffect, useState } from "react";
import { BarraCobertura } from "@/components/BarraCobertura";
import { LeyendaEvidencia } from "@/components/LeyendaEvidencia";
import { LienzoMapa } from "@/components/LienzoMapa";
import { PanelFicha } from "@/components/PanelFicha";
import { TablaPasos } from "@/components/TablaPasos";
import { descargarCobertura } from "@/lib/cliente";
import type { Cobertura } from "@/lib/tipos/cobertura";
import type { VistaVia as Vista } from "@/lib/vista-via";

export type Seleccion = { tipo: "paso"; id: string } | { tipo: "compuesto"; id: string } | null;

type Descarga = { taxon: string; cobertura: Cobertura } | { taxon: string; error: true };

/** Mapa, selector de organismo, cobertura, ficha y tabla de una vía. Estado en la URL. */
export function VistaVia({ vista }: { vista: Vista }) {
  const [org, setOrg] = useQueryState("org", parseAsString);
  const [paso, setPaso] = useQueryState("paso", parseAsString);
  const [compuesto, setCompuesto] = useQueryState("compuesto", parseAsString);
  const [descarga, setDescarga] = useState<Descarga | null>(null);

  const taxon = org && vista.organismos.some((o) => o.id === `taxon:${org}`) ? `taxon:${org}` : null;
  useEffect(() => {
    if (!taxon) return;
    let vigente = true;
    descargarCobertura(vista.version, vista.slug, taxon)
      .then((cobertura) => vigente && setDescarga({ taxon, cobertura }))
      .catch(() => vigente && setDescarga({ taxon, error: true }));
    return () => {
      vigente = false;
    };
  }, [taxon, vista.slug, vista.version]);

  const actual = taxon && descarga?.taxon === taxon ? descarga : null;
  const cobertura = actual && "cobertura" in actual ? actual.cobertura : null;
  const estado = !taxon ? "ninguno" : !actual ? "cargando" : cobertura ? "listo" : "error";
  const seleccion: Seleccion =
    paso && vista.pasos.some((p) => p.id === paso)
      ? { tipo: "paso", id: paso }
      : compuesto && vista.compuestos[compuesto]
        ? { tipo: "compuesto", id: compuesto }
        : null;
  const seleccionar = (nueva: Seleccion) => {
    void setPaso(nueva?.tipo === "paso" ? nueva.id : null);
    void setCompuesto(nueva?.tipo === "compuesto" ? nueva.id : null);
  };
  const organismo = vista.organismos.find((o) => o.id === taxon) ?? null;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end gap-4 rounded-[10px] border border-borde bg-superficie p-4">
        <label className="flex flex-col gap-1">
          <span className="text-sm font-semibold">Organismo</span>
          <select
            className="min-w-72 rounded-[6px] border border-borde bg-superficie px-3 py-2"
            value={org ?? ""}
            onChange={(e) => void setOrg(e.target.value || null)}
          >
            <option value="">Ninguno (solo la vía de referencia)</option>
            {vista.organismos.map((o) => (
              <option key={o.id} value={o.id.replace("taxon:", "")}>
                {o.nombre}
              </option>
            ))}
          </select>
        </label>
        <div className="min-w-64 flex-1" aria-live="polite">
          {estado === "ninguno" && (
            <p className="text-sm text-tinta-suave">
              Elige un organismo para colorear cada paso según la evidencia de que tiene la
              enzima.
            </p>
          )}
          {estado === "cargando" && <p className="text-sm">Cargando la cobertura…</p>}
          {estado === "error" && (
            <p className="text-sm" role="alert">
              No pudimos descargar la cobertura de este organismo. Recarga la página para intentar
              de nuevo.
            </p>
          )}
          {cobertura && organismo && (
            <BarraCobertura cobertura={cobertura} organismo={organismo} pasos={vista.pasos} />
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_24rem]">
        <div className="space-y-3">
          {vista.mapa ? (
            <LienzoMapa
              vista={vista}
              cobertura={cobertura}
              seleccion={seleccion}
              onSeleccion={seleccionar}
            />
          ) : (
            <p>Esta vía aún no tiene un mapa dibujado. Consulta la tabla de pasos.</p>
          )}
          <LeyendaEvidencia />
        </div>
        <PanelFicha
          vista={vista}
          seleccion={seleccion}
          cobertura={cobertura}
          organismo={organismo}
          onSeleccion={seleccionar}
        />
      </div>

      <TablaPasos vista={vista} cobertura={cobertura} onSeleccion={seleccionar} />
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { Formula } from "@/components/Formula";
import { Muestra } from "@/components/Muestra";
import type { Seleccion } from "@/components/VistaVia";
import { descargarEnzima } from "@/lib/cliente";
import { MARCA_REGULADO } from "@/lib/estilo-evidencia";
import { nativo } from "@/lib/rutas";
import { EXPLICACION_ESTADO, NOMBRE_ESTADO } from "@/lib/textos";
import type { Cobertura } from "@/lib/tipos/cobertura";
import type { Proteina } from "@/lib/tipos/enzima";
import type { Origen, OrganismoVista, PasoVista, VistaVia } from "@/lib/vista-via";

const NOMBRE_CLASE_QUIMICA = {
  carbohidrato: "Carbohidrato",
  lipido: "Lípido",
  aminoacido: "Aminoácido",
  nucleotido: "Nucleótido",
  cofactor: "Cofactor",
  ion_gas: "Ion o molécula inorgánica",
  otro: "Otro",
} as const;

interface Props {
  vista: VistaVia;
  seleccion: Seleccion;
  cobertura: Cobertura | null;
  organismo: OrganismoVista | null;
  onSeleccion: (s: Seleccion) => void;
  textosPasos: Record<string, string>;
}

/** Panel lateral: resumen de la vía o ficha del paso o compuesto elegido. */
export function PanelFicha({ vista, seleccion, cobertura, organismo, onSeleccion, textosPasos }: Props) {
  return (
    <aside
      aria-labelledby="titulo-ficha"
      className="space-y-3 self-start rounded-[10px] border border-borde bg-superficie p-4"
    >
      {seleccion === null && <Resumen vista={vista} />}
      {seleccion?.tipo === "paso" && (
        <FichaPaso
          vista={vista}
          paso={vista.pasos.find((p) => p.id === seleccion.id)!}
          cobertura={cobertura}
          organismo={organismo}
          onSeleccion={onSeleccion}
          texto={textosPasos[seleccion.id]}
        />
      )}
      {seleccion?.tipo === "compuesto" && (
        <FichaCompuesto vista={vista} id={seleccion.id} onSeleccion={onSeleccion} />
      )}
      {seleccion !== null && (
        <button
          type="button"
          className="rounded-[6px] border border-borde px-3 py-1 text-sm"
          onClick={() => onSeleccion(null)}
        >
          Cerrar ficha
        </button>
      )}
    </aside>
  );
}

function Resumen({ vista }: { vista: VistaVia }) {
  return (
    <>
      <h2 id="titulo-ficha" className="text-2xl font-semibold">
        Resumen
      </h2>
      {vista.modulos.map((m) => (
        <section key={m.id}>
          <h3 className="font-semibold">{m.nombre}</h3>
          {m.resumen && <p className="text-sm">{m.resumen}</p>}
        </section>
      ))}
      <p className="text-sm text-tinta-suave">
        Toca un paso o un compuesto en el mapa o en la tabla para ver su ficha.
      </p>
    </>
  );
}

function Origenes({ origen }: { origen: Origen[] }) {
  return (
    <p className="text-xs text-tinta-suave">
      Fuente:{" "}
      {origen.map((o, i) => (
        <span key={`${o.fuente}-${o.id}`}>
          {i > 0 && "; "}
          {o.url ? <a href={o.url}>{`${o.nombreFuente} ${o.id}`}</a> : `${o.nombreFuente} ${o.id}`},
          versión {o.version}, descargado el {o.fecha}
        </span>
      ))}
      .
    </p>
  );
}

function FichaPaso({
  vista,
  paso,
  cobertura,
  organismo,
  onSeleccion,
  texto,
}: {
  vista: VistaVia;
  texto?: string;
  paso: PasoVista;
  cobertura: Cobertura | null;
  organismo: OrganismoVista | null;
  onSeleccion: (s: Seleccion) => void;
}) {
  const modulo = vista.modulos.find((m) => m.id === paso.modulo);
  const nombre = (id: string) => vista.compuestos[id]?.nombre ?? id;
  const flecha = vista.mapa?.flechas.find((f) => f.paso === paso.id);
  const compuestos = flecha ? [...new Set([...flecha.desde, ...flecha.hacia])] : [];
  return (
    <>
      <p className="text-sm text-tinta-suave">
        Paso {paso.orden}
        {modulo && ` · ${modulo.nombre}`}
      </p>
      <h2 id="titulo-ficha" className="text-2xl font-semibold">
        {paso.titulo}
      </h2>
      {texto && <p>{texto}</p>}
      {paso.regulacion && (
        <p className="text-sm">
          <span aria-hidden="true">{MARCA_REGULADO} </span>Paso regulado: es un punto de control de
          la vía.
        </p>
      )}
      {cobertura && organismo && (
        <Evidencia paso={paso} vista={vista} cobertura={cobertura} organismo={organismo} />
      )}
      <section>
        <h3 className="font-semibold">Enzima</h3>
        {paso.enzimas.map((ec) => {
          const e = vista.enzimas[ec];
          return (
            <div key={ec} className="text-sm">
              <span lang="en">{e?.nombre}</span>{" "}
              <span className="font-mono text-xs">{ec.replace("EC:", "EC ")}</span>
              {e && <Origenes origen={e.origen} />}
            </div>
          );
        })}
      </section>
      <section>
        <h3 className="font-semibold">Reacción</h3>
        {paso.reacciones.map((rid) => {
          const r = vista.reacciones[rid];
          return (
            <div key={rid} className="text-sm">
              <p lang="en">{r?.ecuacion}</p>
              {r && <Origenes origen={r.origen} />}
            </div>
          );
        })}
        {(paso.consume.length > 0 || paso.produce.length > 0) && (
          <p className="text-sm">
            En el sentido de la vía,{" "}
            {[
              paso.consume.length > 0 && `consume ${paso.consume.map(nombre).join(", ")}`,
              paso.produce.length > 0 && `produce ${paso.produce.map(nombre).join(", ")}`,
            ]
              .filter(Boolean)
              .join(" y ")}
            .
          </p>
        )}
      </section>
      {compuestos.length > 0 && (
      <section>
        <h3 className="font-semibold">Compuestos</h3>
        <ul className="flex flex-wrap gap-2 text-sm">
          {compuestos.map((id) => (
            <li key={id}>
              <button
                type="button"
                lang="en"
                className="min-h-6 text-primario underline underline-offset-2"
                onClick={() => onSeleccion({ tipo: "compuesto", id })}
              >
                {nombre(id)}
              </button>
            </li>
          ))}
        </ul>
      </section>
      )}
    </>
  );
}

function Evidencia({
  paso,
  vista,
  cobertura,
  organismo,
}: {
  paso: PasoVista;
  vista: VistaVia;
  cobertura: Cobertura;
  organismo: OrganismoVista;
}) {
  const resultado = cobertura.pasos[paso.id];
  const [proteinas, setProteinas] = useState<Map<string, Proteina>>(new Map());
  useEffect(() => {
    let vigente = true;
    Promise.all(paso.enzimas.map((ec) => descargarEnzima(vista.version, ec).catch(() => null)))
      .then((enzimas) => {
        const porId = new Map<string, Proteina>();
        for (const e of enzimas) {
          for (const p of e?.proteinas ?? []) if (p.taxon === organismo.id) porId.set(p.id, p);
        }
        if (vigente) setProteinas(porId);
      })
      .catch(() => undefined);
    return () => {
      vigente = false;
    };
  }, [paso.enzimas, vista.version, organismo.id]);

  if (!resultado) return null;
  const enlaceProteina = (id: string) =>
    vista.plantillaProteina?.replace("{id}", encodeURIComponent(nativo(id))) ?? null;
  return (
    <section className="space-y-1 rounded-[6px] border border-borde p-3">
      <h3 className="flex items-center gap-2 font-semibold">
        <Muestra estado={resultado.estado} />
        {NOMBRE_ESTADO[resultado.estado]} en <em>{organismo.nombre}</em>
      </h3>
      <p className="text-sm">{EXPLICACION_ESTADO[resultado.estado]}</p>
      {resultado.advertencias?.includes("complejo_verificar_subunidades") && (
        <p className="text-sm">Complejo: verifica que estén todas sus subunidades.</p>
      )}
      {resultado.proteinas.length > 0 && (
        <ul className="space-y-1 text-sm">
          {resultado.proteinas.map((id) => {
            const p = proteinas.get(id);
            const url = enlaceProteina(id);
            return (
              <li key={id}>
                {url ? <a href={url}>{nativo(id)}</a> : nativo(id)}
                {p && (
                  <>
                    {" "}
                    <span lang="en">{p.nombre}</span>
                    {p.genes.length > 0 && <em> ({p.genes[0]})</em>} ·{" "}
                    {p.revisada ? "revisada (Swiss-Prot)" : "no revisada (TrEMBL)"}
                  </>
                )}
              </li>
            );
          })}
        </ul>
      )}
      <p className="text-xs text-tinta-suave">
        Fuente: UniProtKB {cobertura.fuentes.uniprot}, calculado el {cobertura.calculado}.
      </p>
    </section>
  );
}

function FichaCompuesto({
  vista,
  id,
  onSeleccion,
}: {
  vista: VistaVia;
  id: string;
  onSeleccion: (s: Seleccion) => void;
}) {
  const c = vista.compuestos[id]!;
  const pasos = vista.pasos.filter((p) =>
    vista.mapa?.flechas.some(
      (f) => f.paso === p.id && (f.desde.includes(id) || f.hacia.includes(id)),
    ),
  );
  return (
    <>
      <p className="text-sm text-tinta-suave">{NOMBRE_CLASE_QUIMICA[c.clase]}</p>
      <h2 id="titulo-ficha" className="text-2xl font-semibold" lang="en">
        {c.nombre}
      </h2>
      <dl className="grid grid-cols-[auto_1fr] gap-x-3 text-sm">
        <dt className="font-semibold">Nombre en ChEBI</dt>
        <dd lang="en">{c.nombreChebi}</dd>
        {c.formula && (
          <>
            <dt className="font-semibold">Fórmula</dt>
            <dd>
              <Formula formula={c.formula} />
            </dd>
          </>
        )}
        {c.carga !== null && (
          <>
            <dt className="font-semibold">Carga</dt>
            <dd>{c.carga}</dd>
          </>
        )}
        {c.masa !== null && (
          <>
            <dt className="font-semibold">Masa monoisotópica</dt>
            <dd>{c.masa.toLocaleString("es")} Da</dd>
          </>
        )}
      </dl>
      {c.definicion && (
        <p className="text-sm" lang="en">
          {c.definicion}
        </p>
      )}
      <p className="text-xs text-tinta-suave">
        La fórmula y la carga son las de la forma predominante a pH 7,3, la que usa Rhea.
      </p>
      <Origenes origen={c.origen} />
      {pasos.length > 0 && (
        <section>
          <h3 className="font-semibold">Pasos donde participa</h3>
          <ul className="space-y-1 text-sm">
            {pasos.map((p) => (
              <li key={p.id}>
                <button
                  type="button"
                  className="min-h-6 text-left text-primario underline underline-offset-2"
                  onClick={() => onSeleccion({ tipo: "paso", id: p.id })}
                >
                  {p.orden}. {p.titulo}
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}

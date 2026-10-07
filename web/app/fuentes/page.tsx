import type { Metadata } from "next";
import { Paquete } from "@/lib/datos";
import { leerFuentes } from "@/lib/fuentes";

export const metadata: Metadata = {
  title: "Fuentes y licencias",
  description: "Bases de datos que usa MetaboAtlas, con su licencia, su versión y cómo citarlas.",
};

export default function FuentesPage() {
  const fuentes = leerFuentes();
  const manifiesto = Paquete.actual().manifiesto();
  const usadas = new Map<string, { version: string; fecha: string }>();
  for (const d of manifiesto.descargas) {
    usadas.set(d.fuente, { version: d.version, fecha: d.fecha_descarga });
  }
  return (
    <div className="max-w-[70ch] space-y-6">
      <h1 className="text-4xl font-semibold">Fuentes y licencias</h1>
      <p>
        MetaboAtlas solo redistribuye datos de bases con licencia abierta verificada. El paquete de
        datos {manifiesto.version_datos} usa estas versiones:
      </p>
      {[...usadas].map(([clave, uso]) => {
        const f = fuentes[clave];
        if (!f) return null;
        return (
          <section
            key={clave}
            aria-labelledby={`fuente-${clave}`}
            className="space-y-2 rounded-[10px] border border-borde bg-superficie p-4"
          >
            <h2 id={`fuente-${clave}`} className="text-2xl font-semibold">
              {f.url ? <a href={f.url}>{f.nombre}</a> : f.nombre}
            </h2>
            <p className="text-sm text-tinta-suave">
              Versión {uso.version}, descargada el {uso.fecha}.
            </p>
            <p>
              Licencia:{" "}
              {f.licencia_url ? <a href={f.licencia_url}>{f.licencia}</a> : f.licencia}.{" "}
              {f.condicion}
            </p>
            {f.cita_recomendada && (
              <figure>
                <figcaption className="text-sm font-semibold">Cómo citar</figcaption>
                <blockquote className="whitespace-pre-line border-l-4 border-borde pl-3 text-sm">
                  {f.cita_recomendada}
                </blockquote>
                {f.doi_cita && (
                  <a className="text-sm" href={`https://doi.org/${f.doi_cita}`}>
                    doi:{f.doi_cita}
                  </a>
                )}
              </figure>
            )}
          </section>
        );
      })}
    </div>
  );
}

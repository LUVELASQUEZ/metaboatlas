import Link from "next/link";
import { type Fuentes, verificada } from "@/lib/fuentes";

/** Fuentes y versiones de los datos de una vía, con su licencia y cómo citarlas. */
export function CajaFuentes({
  fuentes,
  versiones,
}: {
  fuentes: Fuentes;
  versiones: Record<string, string>;
}) {
  const usadas = Object.entries(versiones).filter(([clave]) => verificada(fuentes[clave]));
  return (
    <section
      aria-labelledby="titulo-fuentes"
      className="space-y-3 rounded-[10px] border border-borde bg-superficie p-4"
    >
      <h2 id="titulo-fuentes" className="text-2xl font-semibold">
        Fuentes de esta vía
      </h2>
      <ul className="space-y-2 text-sm">
        {usadas.map(([clave, version]) => {
          const f = fuentes[clave]!;
          return (
            <li key={clave}>
              <strong>{f.url ? <a href={f.url}>{f.nombre}</a> : f.nombre}</strong>, versión{" "}
              {version}. Licencia{" "}
              {f.licencia_url ? <a href={f.licencia_url}>{f.licencia}</a> : f.licencia}.
              {f.doi_cita && (
                <>
                  {" "}
                  Cita: <a href={`https://doi.org/${f.doi_cita}`}>doi:{f.doi_cita}</a>.
                </>
              )}
            </li>
          );
        })}
      </ul>
      <p className="text-sm">
        Las citas completas y las condiciones de cada licencia están en{" "}
        <Link href="/fuentes/">Fuentes y licencias</Link>.
      </p>
    </section>
  );
}

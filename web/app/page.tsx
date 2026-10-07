import Link from "next/link";
import { Paquete } from "@/lib/datos";
import { NOMBRE_EDITORIAL } from "@/lib/textos";

export default function Inicio() {
  const paquete = Paquete.actual();
  const vias = paquete.slugsVias().map((slug) => ({ slug, via: paquete.via(slug) }));
  return (
    <div className="space-y-8">
      <section className="max-w-[70ch] space-y-3">
        <h1 className="text-4xl font-semibold">Mapas metabólicos abiertos</h1>
        <p className="text-lg">
          Explora las vías del metabolismo y descubre qué tan bien están anotadas en distintos
          organismos. Todos los datos vienen de bases de licencia abierta y cada uno muestra su
          fuente.
        </p>
      </section>
      <section aria-labelledby="titulo-vias" className="space-y-4">
        <h2 id="titulo-vias" className="text-2xl font-semibold">
          Vías
        </h2>
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {vias.map(({ slug, via }) => (
            <li
              key={slug}
              className="rounded-[10px] border border-borde bg-superficie p-4 shadow-sm"
            >
              <h3 className="text-xl font-semibold">
                <Link href={`/via/${slug}/`}>{via.nombre.es}</Link>
              </h3>
              <p className="text-sm text-tinta-suave">
                {via.nombre.en} · {via.pasos.length} pasos ·{" "}
                {NOMBRE_EDITORIAL[via.estado_editorial]}
              </p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

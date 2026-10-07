import type { Metadata } from "next";
import Link from "next/link";
import { compilarContenido } from "@/lib/contenido";
import { Paquete } from "@/lib/datos";
import { leerGlosario, validarTermino } from "@/lib/glosario";
import { nativo } from "@/lib/rutas";
import { NOMBRE_EDITORIAL } from "@/lib/textos";

interface Props {
  params: Promise<{ termino: string }>;
}

export const dynamicParams = false;

export function generateStaticParams() {
  return leerGlosario().map((t) => ({ termino: t.id }));
}

function buscar(id: string) {
  const termino = leerGlosario().find((t) => t.id === id);
  if (!termino) throw new Error(`No existe el término ${id}`);
  return termino;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const t = buscar((await params).termino);
  return { title: `${t.termino} · Glosario`, description: t.breve };
}

export default async function TerminoPage({ params }: Props) {
  const t = buscar((await params).termino);
  const paquete = Paquete.actual();
  const slugs = paquete.slugsVias();
  const errores = validarTermino(t, slugs.map((s) => `via:${s}`));
  if (errores.length > 0) throw new Error(`content/glosario/${t.id}.mdx: ${errores.join("; ")}`);
  const Cuerpo = await compilarContenido(t.cuerpo);
  return (
    <article className="max-w-3xl space-y-4">
      <p className="text-sm">
        <Link href="/glosario/">Glosario</Link>
      </p>
      <header className="space-y-2">
        <h1 className="text-4xl font-semibold">{t.termino}</h1>
        <p className="text-lg">{t.breve}</p>
        <p className="text-sm text-tinta-suave">
          <span className="rounded-[6px] border border-borde px-2 py-0.5">
            {NOMBRE_EDITORIAL[t.estado_editorial]}
          </span>{" "}
          {t.generado_con_ia && "Texto redactado con apoyo de IA. "}
          {t.revisores.length > 0 ? `Revisado por ${t.revisores.join(", ")}.` : "Aún no lo revisa un especialista."}
        </p>
      </header>
      <div className="prosa">
        <Cuerpo />
      </div>
      {t.vias.length > 0 && (
        <section>
          <h2 className="text-2xl font-semibold">Vías relacionadas</h2>
          <ul className="mt-2 list-disc pl-5">
            {t.vias.map((v) => (
              <li key={v}>
                <Link href={`/via/${nativo(v)}/`}>{paquete.via(nativo(v)).nombre.es}</Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </article>
  );
}

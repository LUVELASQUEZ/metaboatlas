import type { Metadata } from "next";
import { Suspense } from "react";
import { CajaFuentes } from "@/components/CajaFuentes";
import { VistaVia } from "@/components/VistaVia";
import { Paquete } from "@/lib/datos";
import { leerFuentes } from "@/lib/fuentes";
import { NOMBRE_EDITORIAL } from "@/lib/textos";
import { construirVistaVia } from "@/lib/vista-via";

interface Props {
  params: Promise<{ slug: string }>;
}

export const dynamicParams = false;

export function generateStaticParams() {
  return Paquete.actual()
    .slugsVias()
    .map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const via = Paquete.actual().via(slug);
  return {
    title: via.nombre.es,
    description: `${via.nombre.es}: pasos, enzimas y cobertura por organismo.`,
  };
}

export default async function ViaPage({ params }: Props) {
  const { slug } = await params;
  const paquete = Paquete.actual();
  const fuentes = leerFuentes();
  const via = paquete.via(slug);
  const vista = construirVistaVia(paquete, fuentes, slug);
  // Versiones de todas las fuentes que alimentan la página: la vía, la cobertura y
  // los organismos.
  const versiones: Record<string, string> = { ...via.fuentes };
  for (const taxon of paquete.taxonesConCobertura(slug)) {
    Object.assign(versiones, paquete.cobertura(slug, taxon).fuentes);
  }
  for (const o of paquete.organismos()) {
    for (const p of o.procedencia) versiones[p.fuente] ??= p.version;
  }
  return (
    <article className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-4xl font-semibold">{via.nombre.es}</h1>
        <p className="text-tinta-suave">
          <span lang="en">{via.nombre.en}</span> · {via.compartimento.join(", ")} ·{" "}
          <span className="rounded-[6px] border border-borde px-2 py-0.5 text-sm">
            {NOMBRE_EDITORIAL[via.estado_editorial]}
          </span>
        </p>
      </header>
      <Suspense fallback={<div className="h-96 animate-pulse rounded-[10px] bg-borde" />}>
        <VistaVia vista={vista} />
      </Suspense>
      <CajaFuentes fuentes={fuentes} versiones={versiones} />
    </article>
  );
}

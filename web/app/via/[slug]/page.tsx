import type { Metadata } from "next";
import { Suspense } from "react";
import { CajaFuentes } from "@/components/CajaFuentes";
import { VistaVia } from "@/components/VistaVia";
import { BalanceEnergetico } from "@/components/contenido/BalanceEnergetico";
import { ContenidoNiveles, NivelActivo } from "@/components/contenido/ContenidoNiveles";
import { Nivel } from "@/components/contenido/Nivel";
import { Autoevaluacion } from "@/components/contenido/Autoevaluacion";
import { RefPendiente } from "@/components/contenido/RefPendiente";
import { Bibliografia, Ref } from "@/components/contenido/Referencias";
import { TerminoGlosario } from "@/components/contenido/TerminoGlosario";
import { compilarContenido, leerContenidoVia, validarContenido } from "@/lib/contenido";
import { leerGlosario } from "@/lib/glosario";
import { leerPreguntas, type Pregunta, validarPreguntas } from "@/lib/preguntas";
import { Paquete } from "@/lib/datos";
import { leerFuentes, plantilla, type Fuentes } from "@/lib/fuentes";
import { NIVEL_INICIAL } from "@/lib/niveles";
import { pmidsCitados, pmidsCurados } from "@/lib/referencias";
import { NOMBRE_EDITORIAL } from "@/lib/textos";
import type { Via } from "@/lib/tipos/via";
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
  const contenido = leerContenidoVia(slug);
  if (contenido) {
    const errores = validarContenido(contenido, via);
    if (errores.length > 0) throw new Error(`content/vias/${slug}.mdx: ${errores.join("; ")}`);
  }
  const citados = contenido ? pmidsCitados(contenido.cuerpo) : [];
  const curados = pmidsCurados();
  const sinCurar = citados.filter((p) => !curados.includes(p));
  if (sinCurar.length > 0) {
    throw new Error(`content/vias/${slug}.mdx cita PMID que no están en curation/referencias.yaml: ${sinCurar.join(", ")}`);
  }
  const referencias = Object.fromEntries(citados.map((p) => [p, paquete.referencia(p)]));
  const autoevaluacion = leerPreguntas(slug);
  if (autoevaluacion) {
    const errores = validarPreguntas(autoevaluacion, via);
    if (errores.length > 0) throw new Error(`content/preguntas/${slug}.json: ${errores.join("; ")}`);
  }
  // Versiones de todas las fuentes que alimentan la página: la vía, la cobertura y
  // los organismos.
  const versiones: Record<string, string> = { ...via.fuentes };
  for (const taxon of paquete.taxonesConCobertura(slug)) {
    Object.assign(versiones, paquete.cobertura(slug, taxon).fuentes);
  }
  for (const o of paquete.organismos()) {
    for (const p of o.procedencia) versiones[p.fuente] ??= p.version;
  }
  // Nombres en español (Wikidata) y datos de cita (Europe PMC).
  for (const entidad of [...Object.values(vista.compuestos), ...Object.values(vista.enzimas)]) {
    for (const o of entidad.origen) versiones[o.fuente] ??= o.version;
  }
  for (const r of Object.values(referencias)) {
    for (const p of r?.procedencia ?? []) versiones[p.fuente] ??= p.version;
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
        <VistaVia vista={vista} textosPasos={contenido?.meta.pasos} />
      </Suspense>
      {contenido ? (
        <Explicacion
          via={via}
          cuerpo={contenido.cuerpo}
          meta={contenido.meta}
          preguntas={autoevaluacion?.preguntas ?? []}
          pmids={citados}
          referencias={referencias}
          fuentes={fuentes}
        />
      ) : (
        <p className="text-tinta-suave">Esta vía aún no tiene explicación didáctica.</p>
      )}
      <CajaFuentes fuentes={fuentes} versiones={versiones} />
    </article>
  );
}

async function Explicacion({
  via,
  cuerpo,
  meta,
  preguntas,
  pmids,
  referencias,
  fuentes,
}: {
  via: Via;
  cuerpo: string;
  meta: NonNullable<ReturnType<typeof leerContenidoVia>>["meta"];
  preguntas: Pregunta[];
  /** En orden de primera cita (las claves numéricas de un objeto se reordenan). */
  pmids: string[];
  referencias: Parameters<typeof Bibliografia>[0]["referencias"];
  fuentes: Fuentes;
}) {
  const numeros = new Map(pmids.map((p, i) => [p, i + 1]));
  const glosario = leerGlosario();
  const breve = Object.fromEntries(glosario.map((t) => [t.id, t.breve]));
  const titulos = Object.fromEntries(via.pasos.map((p) => [p.id, p.titulo]));
  const Contenido = await compilarContenido(cuerpo, glosario);
  const texto = (
    <Contenido
      components={{
        Nivel,
        RefPendiente,
        Ref: ({ pmid }: { pmid: string }) => <Ref pmid={pmid} numeros={numeros} />,
        Bibliografia: () => (
          <Bibliografia
            pmids={pmids}
            referencias={referencias}
            plantillaArticulo={plantilla(fuentes, "europe_pmc", "articulo")}
          />
        ),
        BalanceEnergetico: (props: { duplicados?: string[] }) => <BalanceEnergetico via={via} {...props} />,
        TerminoGlosario: ({ id, children }: { id: string; children: React.ReactNode }) => (
          <TerminoGlosario id={id} breve={breve[id]}>
            {children}
          </TerminoGlosario>
        ),
        Autoevaluacion: () =>
          preguntas.length > 0 ? (
            <Autoevaluacion preguntas={preguntas} titulos={titulos} />
          ) : (
            <p>Esta vía aún no tiene preguntas.</p>
          ),
      }}
    />
  );
  return (
    <section aria-labelledby="titulo-explicacion" className="space-y-3 rounded-[10px] border border-borde bg-superficie p-6">
      <header className="space-y-2">
        <h2 id="titulo-explicacion" className="text-3xl font-semibold">
          Explicación
        </h2>
        <p className="text-sm text-tinta-suave">
          <span className="rounded-[6px] border border-borde px-2 py-0.5">
            {NOMBRE_EDITORIAL[meta.estado_editorial]}
          </span>{" "}
          {meta.generado_con_ia && "Texto redactado con apoyo de IA. "}
          {meta.revisores.length > 0
            ? `Revisado por ${meta.revisores.join(", ")}.`
            : "Aún no lo revisa un especialista."}{" "}
          Actualizado el {meta.actualizado}. Cambia el nivel con el selector de arriba.
        </p>
      </header>
      <Suspense fallback={<NivelActivo nivel={NIVEL_INICIAL}>{texto}</NivelActivo>}>
        <ContenidoNiveles>{texto}</ContenidoNiveles>
      </Suspense>
    </section>
  );
}

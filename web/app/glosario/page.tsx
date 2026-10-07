import type { Metadata } from "next";
import Link from "next/link";
import { leerGlosario } from "@/lib/glosario";

export const metadata: Metadata = {
  title: "Glosario",
  description: "Términos de bioquímica y metabolismo explicados en español.",
};

export default function GlosarioPage() {
  const terminos = leerGlosario();
  return (
    <article className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-4xl font-semibold">Glosario</h1>
        <p className="text-tinta-suave">
          Definiciones breves de los términos que aparecen en las vías. Están en borrador hasta que
          las revise un especialista.
        </p>
      </header>
      <dl className="max-w-3xl space-y-4">
        {terminos.map((t) => (
          <div key={t.id}>
            <dt className="font-semibold">
              <Link href={`/glosario/${t.id}/`}>{t.termino}</Link>
            </dt>
            <dd>{t.breve}</dd>
          </div>
        ))}
      </dl>
    </article>
  );
}

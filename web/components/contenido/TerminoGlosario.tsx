import Link from "next/link";

/** Enlace de un término a su ficha del glosario, con la definición breve al pasar el cursor. */
export function TerminoGlosario({ id, breve, children }: { id: string; breve?: string; children: React.ReactNode }) {
  return (
    <Link href={`/glosario/${id}/`} title={breve} className="termino-glosario">
      {children}
    </Link>
  );
}

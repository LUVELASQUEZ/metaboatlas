import "@fontsource-variable/source-serif-4";
import "@fontsource/atkinson-hyperlegible/400.css";
import "@fontsource/atkinson-hyperlegible/700.css";
import "@fontsource/jetbrains-mono/400.css";
import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";
import { NuqsAdapter } from "nuqs/adapters/next/app";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: { default: "MetaboAtlas", template: "%s · MetaboAtlas" },
  description:
    "Mapas metabólicos abiertos y didácticos, en español, construidos con datos de licencia abierta.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen">
        <a
          href="#contenido"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:bg-superficie focus:p-2"
        >
          Saltar al contenido
        </a>
        <header className="border-b border-borde bg-superficie">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
            <Link href="/" className="font-serif text-xl font-semibold text-tinta no-underline">
              MetaboAtlas
            </Link>
            <nav aria-label="Principal" className="flex gap-4">
              <Link href="/glosario/">Glosario</Link>
              <Link href="/fuentes/">Fuentes y licencias</Link>
            </nav>
          </div>
        </header>
        <NuqsAdapter>
          <main id="contenido" className="mx-auto max-w-7xl px-4 py-6">
            {children}
          </main>
        </NuqsAdapter>
        <footer className="border-t border-borde px-4 py-6 text-sm text-tinta-suave">
          <div className="mx-auto max-w-7xl">
            Datos de Rhea, ChEBI, UniProtKB, ENZYME y NCBI Taxonomy, con su licencia y cita en{" "}
            <Link href="/fuentes/">Fuentes y licencias</Link>. La falta de anotación no prueba que
            un organismo carezca de una enzima.
          </div>
        </footer>
      </body>
    </html>
  );
}

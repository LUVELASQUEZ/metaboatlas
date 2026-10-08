// Lectura del paquete de datos al construir el sitio (componentes de servidor).
// `npm run datos` deja en public/datos/<version>/ una copia validada contra schema/.
import { existsSync, readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { archivoDe } from "@/lib/rutas";
import type { Cobertura } from "@/lib/tipos/cobertura";
import type { Compuesto } from "@/lib/tipos/compuesto";
import type { EnzimaActividad as Enzima } from "@/lib/tipos/enzima";
import type { Manifiesto } from "@/lib/tipos/manifiesto";
import type { Mapa } from "@/lib/tipos/mapa";
import type { Organismo } from "@/lib/tipos/organismo";
import type { Reaccion } from "@/lib/tipos/reaccion";
import type { ReferenciaBibliografica as Referencia } from "@/lib/tipos/referencia";
import type { Via } from "@/lib/tipos/via";

export class Paquete {
  constructor(
    readonly dir: string,
    readonly version: string,
  ) {}

  /** El paquete que dejó `npm run datos` en public/datos/. */
  static actual(raiz = path.join(process.cwd(), "public", "datos")): Paquete {
    const archivo = path.join(raiz, "version.json");
    if (!existsSync(archivo)) {
      throw new Error("Falta public/datos/version.json: corre `npm run datos` antes de construir.");
    }
    const { version } = JSON.parse(readFileSync(archivo, "utf8")) as { version: string };
    return new Paquete(path.join(raiz, version), version);
  }

  private leer<T>(relativo: string): T {
    return JSON.parse(readFileSync(path.join(this.dir, relativo), "utf8")) as T;
  }

  private existe(relativo: string): boolean {
    return existsSync(path.join(this.dir, relativo));
  }

  private listar(carpeta: string): string[] {
    const dir = path.join(this.dir, carpeta);
    if (!existsSync(dir)) return [];
    return readdirSync(dir)
      .filter((f) => f.endsWith(".json"))
      .map((f) => f.slice(0, -".json".length))
      .sort();
  }

  manifiesto(): Manifiesto {
    return this.leer("manifest.json");
  }

  slugsVias(): string[] {
    return this.listar("vias");
  }

  via(slug: string): Via {
    return this.leer(`vias/${slug}.json`);
  }

  mapa(slug: string): Mapa | null {
    return this.existe(`mapas/${slug}.json`) ? this.leer(`mapas/${slug}.json`) : null;
  }

  compuesto(id: string): Compuesto {
    return this.leer(`compuestos/${archivoDe(id)}.json`);
  }

  reaccion(id: string): Reaccion {
    return this.leer(`reacciones/${archivoDe(id)}.json`);
  }

  enzima(id: string): Enzima {
    return this.leer(`enzimas/${archivoDe(id)}.json`);
  }

  /** Datos de cita de un artículo (Europe PMC); null si el paquete aún no lo trae. */
  referencia(pmid: string): Referencia | null {
    const relativo = `referencias/PMID_${pmid}.json`;
    return this.existe(relativo) ? this.leer(relativo) : null;
  }

  organismos(): Organismo[] {
    return this.listar("organismos").map((t) => this.leer<Organismo>(`organismos/${t}.json`));
  }

  /** Taxones con cobertura calculada para una vía. */
  taxonesConCobertura(slug: string): string[] {
    return this.listar(`cobertura/${slug}`).map((t) => `taxon:${t}`);
  }

  cobertura(slug: string, taxon: string): Cobertura {
    return this.leer(`cobertura/${slug}/${taxon.replace("taxon:", "")}.json`);
  }
}

// Registro de fuentes (sources.yaml): licencia, cita y plantillas de enlace. Se lee
// al construir el sitio. Solo se enlazan las fuentes con licencia verificada.
import { readFileSync } from "node:fs";
import path from "node:path";
import { parse } from "yaml";

export interface Fuente {
  clave: string;
  nombre: string;
  uso: "redistribuir" | "por_verificar" | "solo_enlace";
  estado: string;
  url: string | null;
  licencia: string;
  licencia_url: string | null;
  verificada: string | null;
  condicion: string | null;
  plantillas: Record<string, string>;
  cita_recomendada: string | null;
  doi_cita: string | null;
}

export type Fuentes = Record<string, Fuente>;

export function leerFuentes(
  archivo = path.join(process.cwd(), "..", "sources.yaml"),
): Fuentes {
  const data = parse(readFileSync(archivo, "utf8")) as Record<string, Omit<Fuente, "clave">>;
  return Object.fromEntries(
    Object.entries(data).map(([clave, f]) => [
      clave,
      { ...f, clave, plantillas: f.plantillas ?? {} },
    ]),
  );
}

export function verificada(fuente: Fuente | undefined): fuente is Fuente {
  return fuente?.estado === "verificada";
}

/** Plantilla de URL (`{id}` es el ID nativo), o null si la fuente no está verificada. */
export function plantilla(fuentes: Fuentes, clave: string, tipo: string): string | null {
  const fuente = fuentes[clave];
  return (verificada(fuente) && fuente.plantillas[tipo]) || null;
}

/** URL hacia la página de `id` en una fuente, o null si la fuente no está verificada. */
export function enlace(fuentes: Fuentes, clave: string, tipo: string, id: string): string | null {
  return plantilla(fuentes, clave, tipo)?.replace("{id}", encodeURIComponent(id)) ?? null;
}

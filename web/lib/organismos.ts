import type { OrganismoVista } from "@/lib/vista-via";

/** Grupos del selector de organismos, en este orden; cada organismo va en el de su primer interés. */
export const GRUPOS_ORGANISMOS = [
  { interes: "modelo", etiqueta: "Organismos modelo" },
  { interes: "clinico", etiqueta: "Interés clínico" },
  { interes: "industrial", etiqueta: "Interés industrial y alimentario" },
] as const;

/** Organismos agrupados por su primer interés y ordenados por nombre; omite los grupos vacíos. */
export function agruparOrganismos(organismos: OrganismoVista[]) {
  return GRUPOS_ORGANISMOS.map((g) => ({
    etiqueta: g.etiqueta,
    organismos: organismos
      .filter((o) => o.intereses[0] === g.interes)
      .sort((a, b) => a.nombre.localeCompare(b.nombre, "es")),
  })).filter((g) => g.organismos.length > 0);
}

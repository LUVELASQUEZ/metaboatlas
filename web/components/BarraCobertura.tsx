import { Muestra } from "@/components/Muestra";
import type { Estado } from "@/lib/cobertura";
import type { Cobertura } from "@/lib/tipos/cobertura";
import {
  ADVERTENCIA_COBERTURA,
  ESTADOS,
  MENSAJE_CLASE,
  NOMBRE_CLASE,
  NOMBRE_ESTADO,
} from "@/lib/textos";
import type { OrganismoVista, PasoVista } from "@/lib/vista-via";

/** Porcentaje de cobertura, su clase y el desglose de pasos por evidencia. */
export function BarraCobertura({
  cobertura,
  organismo,
  pasos,
}: {
  cobertura: Cobertura;
  organismo: OrganismoVista;
  pasos: PasoVista[];
}) {
  const conteo = new Map<Estado, number>();
  for (const p of pasos) {
    const estado = cobertura.pasos[p.id]?.estado ?? "sin_anotacion";
    conteo.set(estado, (conteo.get(estado) ?? 0) + 1);
  }
  return (
    <div className="space-y-2">
      <p>
        <strong className="text-2xl">{cobertura.cobertura.toLocaleString("es")} %</strong>{" "}
        <span className="font-semibold">{NOMBRE_CLASE[cobertura.clase]}</span> en{" "}
        <em>{organismo.nombre}</em>. {MENSAJE_CLASE[cobertura.clase]}
      </p>
      <div
        className="h-2 overflow-hidden rounded-full bg-borde"
        role="img"
        aria-label={`Cobertura de ${cobertura.cobertura.toLocaleString("es")} %`}
      >
        <div
          className="h-full bg-primario"
          style={{ width: `${Math.min(cobertura.cobertura, 100)}%` }}
        />
      </div>
      <ul className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
        {ESTADOS.filter((e) => conteo.has(e)).map((estado) => (
          <li key={estado} className="flex items-center gap-1">
            <Muestra estado={estado} />
            {NOMBRE_ESTADO[estado]}: {conteo.get(estado)}
          </li>
        ))}
      </ul>
      <p className="text-sm text-tinta-suave">{ADVERTENCIA_COBERTURA}</p>
    </div>
  );
}

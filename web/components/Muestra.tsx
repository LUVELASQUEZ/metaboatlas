import type { Estado } from "@/lib/cobertura";
import { ESTILO_EVIDENCIA } from "@/lib/estilo-evidencia";

/** Pequeño rótulo con el color y el patrón de borde de un estado de evidencia. */
export function Muestra({ estado }: { estado: Estado | "neutro" }) {
  const estilo = ESTILO_EVIDENCIA[estado];
  return (
    <span
      aria-hidden="true"
      className="inline-block h-4 w-7 shrink-0 rounded-[4px] bg-superficie align-middle"
      style={{
        borderColor: `var(${estilo.variable})`,
        borderStyle: estilo.borde,
        borderWidth: Math.max(estilo.ancho, 1.5),
      }}
    />
  );
}

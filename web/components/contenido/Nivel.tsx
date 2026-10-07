import { NOMBRE_NIVEL, type Nivel as TipoNivel } from "@/lib/niveles";

/** Bloque de texto de un nivel. Se muestra solo si coincide con el nivel elegido. */
export function Nivel({ nivel, children }: { nivel: TipoNivel; children: React.ReactNode }) {
  return (
    <section data-nivel={nivel} aria-label={`Nivel ${NOMBRE_NIVEL[nivel].toLowerCase()}`}>
      {children}
    </section>
  );
}

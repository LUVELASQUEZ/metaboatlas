"use client";

import { useQueryState } from "nuqs";
import type { Nivel } from "@/lib/niveles";
import { parseNivel } from "@/lib/niveles-url";

/** Muestra solo el bloque del nivel elegido en la URL (los demás quedan ocultos por CSS). */
export function ContenidoNiveles({ children }: { children: React.ReactNode }) {
  const [nivel] = useQueryState("nivel", parseNivel);
  return <NivelActivo nivel={nivel}>{children}</NivelActivo>;
}

export function NivelActivo({ nivel, children }: { nivel: Nivel; children: React.ReactNode }) {
  return (
    <div className="prosa" data-nivel-activo={nivel}>
      {children}
    </div>
  );
}

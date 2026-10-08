"use client";

import { parseAsStringLiteral, useQueryState } from "nuqs";
import { useEffect } from "react";
import { NIVELES, NOMBRE_NIVEL, PREGUNTA_NIVEL, type Nivel } from "@/lib/niveles";
import { parseNivel } from "@/lib/niveles-url";

const CLAVE = "metaboatlas:nivel";

/** Último nivel elegido en este navegador; null si no hay o no se puede leer. */
function nivelGuardado(): Nivel | null {
  try {
    const valor = localStorage.getItem(CLAVE);
    return NIVELES.find((n) => n === valor) ?? null;
  } catch {
    return null;
  }
}

function guardarNivel(nivel: Nivel) {
  try {
    localStorage.setItem(CLAVE, nivel);
  } catch {
    // Sin almacenamiento (modo privado, bloqueado): el nivel queda solo en la URL.
  }
}

/**
 * Básico, intermedio o avanzado. Cambia el texto y el detalle del mapa. Recuerda la
 * elección en este navegador; un nivel escrito en la URL (un enlace compartido) manda.
 */
export function SelectorNivel() {
  const [nivel, setNivel] = useQueryState("nivel", parseNivel);
  const [enUrl] = useQueryState("nivel", parseAsStringLiteral(NIVELES));
  useEffect(() => {
    if (enUrl) return;
    const guardado = nivelGuardado();
    if (guardado && guardado !== nivel) void setNivel(guardado, { history: "replace" });
    // Solo al llegar a la página.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return (
    <fieldset className="flex flex-col gap-1">
      <legend className="text-sm font-semibold">Nivel</legend>
      <div className="flex overflow-hidden rounded-[6px] border border-borde">
        {NIVELES.map((n) => (
          <label
            key={n}
            title={PREGUNTA_NIVEL[n]}
            className="cursor-pointer border-borde px-3 py-2 not-first:border-l has-checked:bg-primario has-checked:text-superficie has-focus-visible:outline-3 has-focus-visible:outline-primario"
          >
            <input
              type="radio"
              name="nivel"
              value={n}
              className="sr-only"
              checked={nivel === n}
              onChange={() => {
                guardarNivel(n);
                void setNivel(n);
              }}
            />
            {NOMBRE_NIVEL[n]}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

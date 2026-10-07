"use client";

import { useQueryState } from "nuqs";
import { NIVELES, NOMBRE_NIVEL, PREGUNTA_NIVEL } from "@/lib/niveles";
import { parseNivel } from "@/lib/niveles-url";

/** Básico, intermedio o avanzado. Cambia el texto y el detalle del mapa. */
export function SelectorNivel() {
  const [nivel, setNivel] = useQueryState("nivel", parseNivel);
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
              onChange={() => void setNivel(n)}
            />
            {NOMBRE_NIVEL[n]}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

import { Muestra } from "@/components/Muestra";
import { MARCA_REGULADO } from "@/lib/estilo-evidencia";
import { ESTADOS, NOMBRE_ESTADO, PATRON_ESTADO } from "@/lib/textos";

/** Explica los colores y patrones del mapa. */
export function LeyendaEvidencia() {
  return (
    <details className="rounded-[10px] border border-borde bg-superficie p-3 text-sm" open>
      <summary className="cursor-pointer font-semibold">Cómo leer el mapa</summary>
      <ul className="mt-2 grid gap-1 sm:grid-cols-2">
        {ESTADOS.filter((e) => e !== "espontaneo").map((estado) => (
          <li key={estado} className="flex items-center gap-2">
            <Muestra estado={estado} />
            <span>
              {NOMBRE_ESTADO[estado]} ({PATRON_ESTADO[estado]})
            </span>
          </li>
        ))}
        <li className="flex items-center gap-2">
          <Muestra estado="neutro" />
          <span>Sin organismo elegido</span>
        </li>
        <li className="flex items-center gap-2">
          <span aria-hidden="true" className="inline-block w-7 text-center">
            {MARCA_REGULADO}
          </span>
          <span>Paso regulado (punto de control), con borde más grueso</span>
        </li>
      </ul>
      <p className="mt-2 text-tinta-suave">
        Los círculos son los metabolitos, coloreados según su clase química. Los cofactores (ATP,
        NAD⁺, agua…) se escriben junto a cada flecha. Los nombres de compuestos y enzimas están en inglés, como en Rhea y ENZYME,
        mientras preparamos su traducción.
      </p>
    </details>
  );
}

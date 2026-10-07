"use client";

import { Check, ChevronDown, ChevronUp, X } from "lucide-react";
import { useState } from "react";
import { NOMBRE_NIVEL } from "@/lib/niveles";
import type { OpcionMultiple, OrdenarPasos, Pregunta } from "@/lib/preguntas";

/** Preguntas de autoevaluación. Se corrigen aquí mismo; no se guarda ningún resultado. */
export function Autoevaluacion({ preguntas, titulos }: { preguntas: Pregunta[]; titulos: Record<string, string> }) {
  return (
    <ol className="list-none space-y-4 p-0">
      {preguntas.map((p) => (
        <li key={p.id} data-nivel={p.nivel} className="rounded-[10px] border border-borde p-4">
          {p.tipo === "opcion_multiple" ? (
            <PreguntaOpciones pregunta={p} />
          ) : (
            <PreguntaOrdenar pregunta={p} titulos={titulos} />
          )}
        </li>
      ))}
    </ol>
  );
}

function Resultado({ correcto, explicacion }: { correcto: boolean; explicacion: string }) {
  const Icono = correcto ? Check : X;
  return (
    <p className="mt-2 flex gap-2">
      <Icono aria-hidden="true" className="mt-1 size-4 shrink-0" />
      <span>
        <strong>{correcto ? "Correcto." : "No es correcto."}</strong> {explicacion}
      </span>
    </p>
  );
}

function Etiqueta({ pregunta }: { pregunta: Pregunta }) {
  return <span className="text-sm text-tinta-suave">Nivel {NOMBRE_NIVEL[pregunta.nivel].toLowerCase()}</span>;
}

function PreguntaOpciones({ pregunta }: { pregunta: OpcionMultiple }) {
  const [elegida, setElegida] = useState<number | null>(null);
  const [revisada, setRevisada] = useState(false);
  return (
    <fieldset>
      <legend className="font-semibold">{pregunta.enunciado}</legend>
      <Etiqueta pregunta={pregunta} />
      <div className="mt-2 space-y-1">
        {pregunta.opciones.map((o, i) => (
          <label key={o} className="flex min-h-6 cursor-pointer items-start gap-2">
            <input
              type="radio"
              name={`pregunta-${pregunta.id}`}
              className="mt-1.5"
              checked={elegida === i}
              onChange={() => {
                setElegida(i);
                setRevisada(false);
              }}
            />
            {o}
          </label>
        ))}
      </div>
      <button
        type="button"
        className="mt-2 min-h-6 rounded-[6px] border border-borde px-3 py-1 text-sm disabled:opacity-60"
        disabled={elegida === null}
        onClick={() => setRevisada(true)}
      >
        Comprobar
      </button>
      <div aria-live="polite">
        {revisada && elegida !== null && (
          <Resultado correcto={elegida === pregunta.correcta} explicacion={pregunta.explicacion} />
        )}
      </div>
    </fieldset>
  );
}

/** Orden inicial fijo y distinto del correcto (igual en el servidor y en el navegador). */
export function desordenar(ids: string[], semilla: string): string[] {
  const peso = (s: string) => [...s].reduce((h, c) => (h * 31 + c.charCodeAt(0)) % 1000003, 7);
  const mezcla = [...ids].sort((a, b) => peso(semilla + a) - peso(semilla + b));
  return mezcla.every((id, i) => id === ids[i]) ? [...ids].reverse() : mezcla;
}

function PreguntaOrdenar({ pregunta, titulos }: { pregunta: OrdenarPasos; titulos: Record<string, string> }) {
  const [orden, setOrden] = useState(() => desordenar(pregunta.pasos, pregunta.id));
  const [revisada, setRevisada] = useState(false);
  const mover = (i: number, d: -1 | 1) => {
    const nuevo = [...orden];
    [nuevo[i], nuevo[i + d]] = [nuevo[i + d]!, nuevo[i]!];
    setOrden(nuevo);
    setRevisada(false);
  };
  const correcto = orden.every((id, i) => id === pregunta.pasos[i]);
  return (
    <div role="group" aria-labelledby={`enunciado-${pregunta.id}`}>
      <p id={`enunciado-${pregunta.id}`} className="font-semibold">
        {pregunta.enunciado}
      </p>
      <Etiqueta pregunta={pregunta} />
      <ol className="mt-2 space-y-1">
        {orden.map((id, i) => {
          const bien = revisada && id === pregunta.pasos[i];
          return (
            <li key={id} className="flex items-center gap-2">
              <span className="w-6 text-right tabular-nums">{i + 1}.</span>
              <span className="flex-1">
                {titulos[id] ?? id}
                {revisada && <span className="text-sm text-tinta-suave"> ({bien ? "en su lugar" : "fuera de lugar"})</span>}
              </span>
              <button
                type="button"
                className="min-h-6 min-w-6 rounded-[6px] border border-borde disabled:opacity-40"
                disabled={i === 0}
                aria-label={`Subir «${titulos[id] ?? id}»`}
                onClick={() => mover(i, -1)}
              >
                <ChevronUp aria-hidden="true" className="mx-auto size-4" />
              </button>
              <button
                type="button"
                className="min-h-6 min-w-6 rounded-[6px] border border-borde disabled:opacity-40"
                disabled={i === orden.length - 1}
                aria-label={`Bajar «${titulos[id] ?? id}»`}
                onClick={() => mover(i, 1)}
              >
                <ChevronDown aria-hidden="true" className="mx-auto size-4" />
              </button>
            </li>
          );
        })}
      </ol>
      <button
        type="button"
        className="mt-2 min-h-6 rounded-[6px] border border-borde px-3 py-1 text-sm"
        onClick={() => setRevisada(true)}
      >
        Comprobar
      </button>
      <div aria-live="polite">{revisada && <Resultado correcto={correcto} explicacion={pregunta.explicacion} />}</div>
    </div>
  );
}

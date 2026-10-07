"use client";

import type { Core, StylesheetJson } from "cytoscape";
import { type KeyboardEvent, useEffect, useMemo, useRef, useState } from "react";
import type { Seleccion } from "@/components/VistaVia";
import { elementosMapa, idCofactores, idPaso, ordenTeclado } from "@/lib/elementos-mapa";
import { ESTILO_EVIDENCIA } from "@/lib/estilo-evidencia";
import type { Cobertura } from "@/lib/tipos/cobertura";
import type { VistaVia } from "@/lib/vista-via";

interface Props {
  vista: VistaVia;
  cobertura: Cobertura | null;
  seleccion: Seleccion;
  onSeleccion: (s: Seleccion) => void;
  /** false en el nivel básico: sin EC ni cofactores. */
  detallado: boolean;
}

const CLASES = ["carbohidrato", "lipido", "aminoacido", "nucleotido", "cofactor", "ion_gas", "otro"];

function token(nombre: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
}

/** Estilos de Cytoscape con los colores del tema actual (claro u oscuro). */
function estilos(): StylesheetJson {
  const tinta = token("--tinta");
  const suave = token("--tinta-suave");
  const superficie = token("--superficie");
  const fuente = "Atkinson Hyperlegible, system-ui, sans-serif";
  return [
    { selector: "*", style: { "z-index-compare": "manual" } },
    {
      selector: 'node[tipo="region"]',
      style: {
        shape: "round-rectangle",
        width: "data(ancho)",
        height: "data(alto)",
        "background-color": superficie,
        "border-color": token("--borde"),
        "border-width": 1,
        label: "data(etiqueta)",
        "text-valign": "top",
        "text-margin-y": 24,
        "font-family": "Source Serif 4 Variable, Georgia, serif",
        "font-size": 16,
        color: suave,
        "z-index": 0,
        events: "no",
      },
    },
    {
      selector: 'node[tipo="compuesto"]',
      style: {
        width: 26,
        height: 26,
        "border-color": tinta,
        "border-width": 1.5,
        label: "data(etiqueta)",
        "font-family": fuente,
        "font-size": 13,
        color: tinta,
        "text-halign": "data(halign)" as never,
        "text-valign": "data(valign)" as never,
        "text-margin-x": "data(mx)" as never,
        "text-margin-y": "data(my)" as never,
        "text-wrap": "wrap",
        "text-max-width": "160",
        "z-index": 10,
      },
    },
    ...CLASES.map((clase) => ({
      selector: `node[clase="${clase}"]`,
      style: { "background-color": token(`--clase-${clase.replace("_", "-")}`) },
    })),
    {
      selector: 'node[tipo="rotulo"]',
      style: {
        shape: "round-rectangle",
        width: "label",
        height: "label",
        padding: "7",
        "background-color": superficie,
        label: "data(etiqueta)",
        "text-wrap": "wrap",
        "text-valign": "center",
        "text-halign": "center",
        "font-family": fuente,
        "font-size": 12,
        color: tinta,
        "z-index": 10,
      },
    },
    ...Object.entries(ESTILO_EVIDENCIA).map(([estado, e]) => ({
      selector: `node[tipo="rotulo"][estado="${estado}"]`,
      style: {
        "border-color": token(e.variable),
        "border-style": e.borde,
        "border-width": e.ancho,
      },
    })),
    { selector: 'node[tipo="rotulo"][estado="sin_anotacion"]', style: { color: suave } },
    { selector: 'node[tipo="rotulo"][?regulado]', style: { "border-width": 5 } },
    {
      selector: 'node[tipo="cofactores"]',
      style: {
        width: 1,
        height: 1,
        "background-opacity": 0,
        label: "data(etiqueta)",
        "font-family": fuente,
        "font-size": 12,
        color: suave,
        "text-halign": "data(halign)" as never,
        "text-valign": "data(valign)" as never,
        "z-index": 10,
      },
    },
    {
      selector: "edge",
      style: { width: 2, "line-color": suave, "curve-style": "straight", "z-index": 5 },
    },
    {
      selector: 'edge[tipo="sale"]',
      style: { "target-arrow-shape": "triangle", "target-arrow-color": suave },
    },
    {
      selector: ".enfocado",
      style: {
        "outline-color": token("--primario"),
        "outline-width": 3,
        "outline-offset": 4,
        "outline-style": "solid",
      } as never,
    },
    {
      selector: ".elegido",
      style: {
        "underlay-color": token("--acento"),
        "underlay-opacity": 0.35,
        "underlay-padding": 6,
        "underlay-shape": "round-rectangle",
      } as never,
    },
  ] as StylesheetJson;
}

/** Ajusta el mapa al lienzo y recuerda ese zoom como el mínimo sin desplazamiento. */
function ajustar(cy: Core) {
  cy.fit(undefined, 16);
  cy.scratch("zoomAjustado", cy.zoom());
  cy.userPanningEnabled(false);
}

/** Coloca los cofactores al lado de su rótulo, según su ancho real. */
function ubicarCofactores(cy: Core) {
  cy.nodes('[tipo="cofactores"]').forEach((n) => {
    const rotulo = cy.getElementById(idPaso(n.data("paso") as string));
    const { x, y } = rotulo.position();
    const ancho = rotulo.outerWidth() / 2 + 8;
    const alto = rotulo.outerHeight() / 2 + 6;
    const desplazamiento: Record<string, [number, number]> = {
      izquierda: [-ancho, 0],
      derecha: [ancho, 0],
      arriba: [0, -alto],
      abajo: [0, alto],
    };
    const [dx, dy] = desplazamiento[n.data("lado") as string] ?? [0, 0];
    n.position({ x: x + dx, y: y + dy });
  });
}

/** Mapa de la vía con Cytoscape.js (diseño `preset`: las posiciones son las curadas). */
export function LienzoMapa({ vista, cobertura, seleccion, onSeleccion, detallado }: Props) {
  const contenedor = useRef<HTMLDivElement>(null);
  const [cy, setCy] = useState<Core | null>(null);
  const alSeleccionar = useRef(onSeleccion);
  useEffect(() => {
    alSeleccionar.current = onSeleccion;
  }, [onSeleccion]);

  // Crea el lienzo una vez; Cytoscape se descarga solo en las páginas con mapa.
  useEffect(() => {
    let instancia: Core | null = null;
    let cancelado = false;
    const tema = window.matchMedia("(prefers-color-scheme: dark)");
    const alCambiarTema = () => instancia?.style(estilos());
    void import("cytoscape").then(({ default: cytoscape }) => {
      if (cancelado || !contenedor.current) return;
      const cy = cytoscape({
        container: contenedor.current,
        elements: [],
        layout: { name: "preset" },
        style: estilos(),
        userZoomingEnabled: false,
        // Sin zoom, arrastrar desplaza la página; con zoom, mueve el mapa.
        userPanningEnabled: false,
        boxSelectionEnabled: false,
        autoungrabify: true,
        autounselectify: true,
        minZoom: 0.3,
        maxZoom: 3,
      });
      cy.on("zoom", () => cy.userPanningEnabled(cy.zoom() > (cy.scratch("zoomAjustado") ?? 1) * 1.01));
      cy.on("tap", "node", (evento) => {
        const n = evento.target;
        const tipo = n.data("tipo");
        if (tipo === "compuesto") alSeleccionar.current({ tipo: "compuesto", id: n.id() });
        else if (tipo === "rotulo" || tipo === "cofactores") {
          alSeleccionar.current({ tipo: "paso", id: n.data("paso") });
        }
      });
      cy.on("mouseover", 'node[tipo!="region"]', () => {
        if (contenedor.current) contenedor.current.style.cursor = "pointer";
      });
      cy.on("mouseout", "node", () => {
        if (contenedor.current) contenedor.current.style.cursor = "";
      });
      instancia = cy;
      tema.addEventListener("change", alCambiarTema);
      setCy(cy);
    });
    return () => {
      cancelado = true;
      tema.removeEventListener("change", alCambiarTema);
      instancia?.destroy();
      setCy(null);
    };
  }, []);

  // Elementos: cambian con el organismo (colores y signos) y con el nivel (detalle).
  useEffect(() => {
    if (!cy) return;
    const primeraVez = cy.elements().length === 0;
    cy.batch(() => {
      cy.elements().remove();
      cy.add(elementosMapa(vista, cobertura, detallado));
    });
    if (primeraVez) ajustar(cy);
    // El ancho de los rótulos se conoce después de dibujarlos con la tipografía final.
    let vigente = true;
    const ubicar = () => vigente && ubicarCofactores(cy);
    ubicar();
    const cuadro = requestAnimationFrame(ubicar);
    void document.fonts.ready.then(ubicar);
    return () => {
      vigente = false;
      cancelAnimationFrame(cuadro);
    };
  }, [cy, vista, cobertura, detallado]);

  // Resalta el elemento elegido.
  const pasoElegido = seleccion?.tipo === "paso" ? seleccion.id : null;
  const compuestoElegido = seleccion?.tipo === "compuesto" ? seleccion.id : null;
  useEffect(() => {
    if (!cy) return;
    cy.elements().removeClass("elegido");
    if (pasoElegido) {
      cy.getElementById(idPaso(pasoElegido)).addClass("elegido");
      cy.getElementById(idCofactores(pasoElegido)).addClass("elegido");
    } else if (compuestoElegido) {
      cy.getElementById(compuestoElegido).addClass("elegido");
    }
  }, [cy, pasoElegido, compuestoElegido, cobertura, detallado]);

  // Teclado: las flechas recorren el mapa en el sentido de la vía y Enter abre la ficha.
  const paradas = useMemo(() => ordenTeclado(vista), [vista]);
  const [foco, setFoco] = useState<number | null>(null);
  const [conTeclado, setConTeclado] = useState(false);
  const parada = foco === null ? null : (paradas[foco] ?? null);
  useEffect(() => {
    if (!cy) return;
    cy.elements().removeClass("enfocado");
    if (!parada) return;
    const nodo = cy.getElementById(parada.id);
    nodo.addClass("enfocado");
    // Con zoom, lleva el elemento a la vista; sin zoom el mapa entero ya está visible.
    if (cy.userPanningEnabled()) cy.center(nodo);
  }, [cy, parada, cobertura, detallado]);

  const alTeclear = (e: KeyboardEvent<HTMLDivElement>) => {
    if (paradas.length === 0) return;
    const actual = foco ?? -1;
    const ir = (i: number) => {
      e.preventDefault();
      setFoco(Math.max(0, Math.min(paradas.length - 1, i)));
    };
    if (e.key === "ArrowRight" || e.key === "ArrowDown") ir(actual + 1);
    else if (e.key === "ArrowLeft" || e.key === "ArrowUp") ir(foco === null ? 0 : actual - 1);
    else if (e.key === "Home") ir(0);
    else if (e.key === "End") ir(paradas.length - 1);
    else if ((e.key === "Enter" || e.key === " ") && parada) {
      e.preventDefault();
      onSeleccion(parada.seleccion);
    } else if (e.key === "Escape") {
      setFoco(null);
      onSeleccion(null);
    }
  };

  const zoom = (factor: number) => {
    if (!cy) return;
    cy.zoom({
      level: cy.zoom() * factor,
      renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 },
    });
  };

  return (
    <div
      className="relative mx-auto overflow-hidden rounded-[10px] border border-borde bg-fondo"
      style={{ maxWidth: vista.mapa!.ancho * 1.25 }}
    >
      <div className="absolute right-2 top-2 z-10 flex gap-1">
        {[
          { texto: "+", etiqueta: "Acercar", accion: () => zoom(1.25) },
          { texto: "−", etiqueta: "Alejar", accion: () => zoom(0.8) },
          { texto: "Ajustar", etiqueta: "Ajustar el mapa a la pantalla", accion: () => cy && ajustar(cy) },
        ].map((b) => (
          <button
            key={b.etiqueta}
            type="button"
            aria-label={b.etiqueta}
            title={b.etiqueta}
            onClick={b.accion}
            className="min-h-9 min-w-9 rounded-[6px] border border-borde bg-superficie px-2 text-sm"
          >
            {b.texto}
          </button>
        ))}
      </div>
      <div
        ref={contenedor}
        tabIndex={0}
        role="application"
        aria-roledescription="mapa"
        aria-label="Mapa de la vía"
        aria-describedby="instrucciones-mapa"
        onKeyDown={alTeclear}
        onFocus={(e) => setConTeclado(e.currentTarget.matches(":focus-visible"))}
        onBlur={() => {
          setFoco(null);
          setConTeclado(false);
        }}
        className="w-full"
        // El lienzo conserva la proporción del dibujo: la página se desplaza, no el mapa.
        style={{ aspectRatio: `${vista.mapa!.ancho} / ${vista.mapa!.alto}` }}
      />
      <p id="instrucciones-mapa" className="sr-only">
        Usa las flechas para recorrer compuestos y pasos en el sentido de la vía, Enter para abrir su
        ficha y Escape para cerrarla. La tabla de pasos, más abajo, tiene la misma información.
      </p>
      {conTeclado && (
        <p aria-hidden="true" className="absolute bottom-2 left-2 rounded-[6px] border border-borde bg-superficie px-2 py-1 text-sm">
          Flechas: recorrer · Enter: abrir ficha · Esc: cerrar
        </p>
      )}
      <p aria-live="polite" className="sr-only">
        {parada?.texto ?? ""}
      </p>
    </div>
  );
}

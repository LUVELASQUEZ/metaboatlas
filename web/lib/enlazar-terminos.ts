// Plugin de remark: envuelve la primera aparición de cada término del glosario en
// <TerminoGlosario id="…">. Cada bloque <Nivel> cuenta como un texto aparte, porque solo
// se ve uno a la vez; el resto del documento (fuera de los niveles) es otro texto.

export interface TerminoEnlazable {
  id: string;
  formas: string[];
}

interface Nodo {
  type: string;
  name?: string | null;
  value?: string;
  children?: Nodo[];
  attributes?: unknown[];
}

// No se enlaza dentro de títulos, enlaces, código ni de otros componentes.
const NO_ENLAZAR = new Set(["heading", "link", "linkReference", "inlineCode", "code"]);

const escapar = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

/** Expresión que encuentra cualquier forma como palabra completa (sin distinguir mayúsculas). */
export function expresionTerminos(terminos: TerminoEnlazable[]): { regex: RegExp; idDe: Map<string, string> } {
  const idDe = new Map<string, string>();
  for (const t of terminos) for (const f of t.formas) idDe.set(f.toLocaleLowerCase("es"), t.id);
  // Las formas largas primero, para que "triosas fosfato" gane a "triosa".
  const formas = [...idDe.keys()].sort((a, b) => b.length - a.length).map(escapar);
  const regex = new RegExp(`(?<![\\p{L}\\p{N}])(?:${formas.join("|")})(?![\\p{L}\\p{N}])`, "giu");
  return { regex, idDe };
}

function enlazarTexto(nodo: Nodo, regex: RegExp, idDe: Map<string, string>, vistos: Set<string>): Nodo[] {
  const texto = nodo.value ?? "";
  const salida: Nodo[] = [];
  let desde = 0;
  for (const m of texto.matchAll(regex)) {
    const id = idDe.get(m[0].toLocaleLowerCase("es"))!;
    if (vistos.has(id)) continue;
    vistos.add(id);
    if (m.index > desde) salida.push({ type: "text", value: texto.slice(desde, m.index) });
    salida.push({
      type: "mdxJsxTextElement",
      name: "TerminoGlosario",
      attributes: [{ type: "mdxJsxAttribute", name: "id", value: id }],
      children: [{ type: "text", value: m[0] }],
    });
    desde = m.index + m[0].length;
  }
  if (salida.length === 0) return [nodo];
  if (desde < texto.length) salida.push({ type: "text", value: texto.slice(desde) });
  return salida;
}

function recorrer(nodo: Nodo, regex: RegExp, idDe: Map<string, string>, vistos: Set<string>): void {
  if (!nodo.children) return;
  const hijos: Nodo[] = [];
  for (const hijo of nodo.children) {
    if (hijo.type === "text") {
      hijos.push(...enlazarTexto(hijo, regex, idDe, vistos));
      continue;
    }
    const componente = hijo.type.startsWith("mdxJsx") && hijo.name !== "Nivel";
    if (!NO_ENLAZAR.has(hijo.type) && !componente) recorrer(hijo, regex, idDe, vistos);
    hijos.push(hijo);
  }
  nodo.children = hijos;
}

export function remarkTerminos(terminos: TerminoEnlazable[]) {
  const { regex, idDe } = expresionTerminos(terminos);
  return (arbol: Nodo) => {
    const comun = new Set<string>();
    for (const hijo of arbol.children ?? []) {
      if (hijo.type === "mdxJsxFlowElement" && hijo.name === "Nivel") recorrer(hijo, regex, idDe, new Set());
      else if (!NO_ENLAZAR.has(hijo.type) && !hijo.type.startsWith("mdxJsx")) recorrer(hijo, regex, idDe, comun);
    }
  };
}

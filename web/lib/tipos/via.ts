// Generado por scripts/generate-types.mjs desde schema/. No editar a mano.

/**
 * Referencias a Reactome, WikiPathways, GO, KEGG (mapa) y MetaCyc, como pares (fuente, id).
 */
export type Xrefs = Xref[];

/**
 * Vía de referencia, independiente del organismo, con sus módulos y pasos. Archivo vias/<slug>.json del paquete de datos (secciones 4 y 6 de docs/MANUAL.md).
 */
export interface Via {
  /**
   * ID propio de una vía, por ejemplo via:glucolisis.
   */
  id: string;
  nombre: TextoBilingueCompleto;
  /**
   * ID propio de una categoría, por ejemplo cat:carbohidratos.
   */
  categoria: string;
  /**
   * Compartimentos donde ocurre la vía (citosol, matriz-mitocondrial, membrana, periplasma, …).
   *
   * @minItems 1
   *
   * Items: Slug en español, sin tildes, en minúsculas y con guiones.
   */
  compartimento: [string, ...string[]];
  /**
   * @minItems 1
   */
  modulos: [Modulo, ...Modulo[]];
  /**
   * @minItems 1
   */
  pasos: [Paso, ...Paso[]];
  /**
   * Vías conectadas por compuestos compartidos.
   *
   * Items: ID propio de una vía, por ejemplo via:glucolisis.
   */
  conecta_con: string[];
  /**
   * Vía de la que esta es una variante (por ejemplo, Entner-Doudoroff respecto de la glucólisis), o null.
   */
  variante_de: string | null;
  xrefs: Xrefs;
  /**
   * Versión del paquete de datos de MetaboAtlas (AAAA.MM).
   */
  version: string;
  estado_editorial: "borrador" | "revisado" | "validado";
  /**
   * Nombres de quienes revisaron o validaron la vía.
   */
  revisores?: string[];
  fuentes: VersionesFuentes;
}
/**
 * Texto en español e inglés, ambos obligatorios (contenido curado).
 */
export interface TextoBilingueCompleto {
  es: string;
  en: string;
}
/**
 * Bloque funcional con sentido didáctico (por ejemplo, la fase preparatoria de la glucólisis).
 */
export interface Modulo {
  /**
   * ID local de un módulo dentro de su vía (m1, m2, …). El ID global es via:<slug>/m1.
   */
  id: string;
  nombre: string;
  /**
   * @minItems 1
   *
   * Items: ID local de un paso dentro de su vía (p01, p02, …). El ID global es via:<slug>/p01.
   */
  pasos: [string, ...string[]];
  /**
   * Resumen didáctico corto en español.
   */
  resumen?: string;
}
/**
 * Una posición en el mapa de una vía de referencia: una o varias reacciones Rhea alternativas catalizadas por una actividad enzimática (sección 4 de docs/MANUAL.md).
 */
export interface Paso {
  /**
   * ID local de un paso dentro de su vía (p01, p02, …). El ID global es via:<slug>/p01.
   */
  id: string;
  /**
   * Posición del paso en el recorrido didáctico, empezando en 1.
   */
  orden: number;
  /**
   * Título corto en español (por ejemplo, 'Fosforilación de la glucosa').
   */
  titulo: string;
  /**
   * Reacciones Rhea válidas para el paso (alternativas). Vacío solo si el paso es espontáneo y no tiene reacción Rhea.
   */
  reacciones: string[];
  /**
   * Números EC de las actividades que catalizan el paso.
   *
   * Items: Número EC completo o parcial (EC:2.7.1.1, EC:2.7.1.-, EC:3.5.1.n3).
   */
  ec: string[];
  /**
   * true si el paso no requiere enzima; en ese caso siempre cuenta como presente.
   */
  espontaneo: boolean;
  /**
   * true si es un punto de regulación de la vía.
   */
  regulacion: boolean;
  /**
   * true si la actividad la realiza un complejo multiproteico (se muestra 'complejo: verificar subunidades').
   */
  complejo?: boolean;
  /**
   * Moléculas de energía o poder reductor consumidas (negativo) o producidas (positivo) en el paso, por ejemplo { "ATP": -1 }.
   */
  energia?: {
    [k: string]: number;
  };
}
/**
 * Referencia cruzada como par (fuente, id). El enlace se construye con la plantilla `tipo` de la fuente en sources.yaml, reemplazando {id}.
 */
export interface Xref {
  /**
   * Clave de una fuente registrada en sources.yaml (rhea, chebi, uniprot, …).
   */
  fuente: string;
  /**
   * Clave de la plantilla de URL en sources.yaml (por ejemplo via_referencia en KEGG).
   */
  tipo: string;
  /**
   * ID nativo en la fuente, sin prefijo CURIE (por ejemplo map00010, C00022, 2.7.1.1).
   */
  id: string;
}
/**
 * Versión de cada fuente con la que se verificó la curaduría (por ejemplo, la versión de Rhea).
 */
export interface VersionesFuentes {
  [k: string]: string;
}

// Generado por scripts/generate-types.mjs desde schema/. No editar a mano.

/**
 * Dibujo curado de una vía: solo posiciones, en píxeles de un lienzo con el origen arriba a la izquierda. Los datos (nombres, reacciones, evidencia) se toman del paquete de datos (sección 7 de docs/MANUAL.md). Archivo curation/mapas/<slug>.json, que se exporta como mapas/<slug>.json.
 */
export interface Mapa {
  /**
   * ID propio de una vía, por ejemplo via:glucolisis.
   */
  via: string;
  lienzo: {
    ancho: number;
    alto: number;
  };
  /**
   * Metabolitos principales, uno por nodo. Los cofactores no van aquí: se dibujan junto a la flecha de cada paso.
   *
   * @minItems 1
   */
  compuestos: [
    {
      compuesto: string;
      x: number;
      y: number;
      /**
       * Lado del nodo donde va el nombre del compuesto.
       */
      etiqueta?: "izquierda" | "derecha" | "arriba" | "abajo";
    },
    ...{
      compuesto: string;
      x: number;
      y: number;
      /**
       * Lado del nodo donde va el nombre del compuesto.
       */
      etiqueta?: "izquierda" | "derecha" | "arriba" | "abajo";
    }[]
  ];
  /**
   * Una flecha por paso de la vía, en el sentido de la vía (no necesariamente el de la reacción maestra de Rhea).
   *
   * @minItems 1
   */
  pasos: [
    {
      /**
       * ID local de un paso dentro de su vía (p01, p02, …). El ID global es via:<slug>/p01.
       */
      paso: string;
      /**
       * @minItems 1
       */
      desde: [string, ...string[]];
      /**
       * @minItems 1
       */
      hacia: [string, ...string[]];
      /**
       * Centro del rótulo de la enzima.
       */
      rotulo: {
        x: number;
        y: number;
      };
      /**
       * Lado de la flecha donde se dibujan los cofactores del paso.
       */
      cofactores: "izquierda" | "derecha" | "arriba" | "abajo";
    },
    ...{
      /**
       * ID local de un paso dentro de su vía (p01, p02, …). El ID global es via:<slug>/p01.
       */
      paso: string;
      /**
       * @minItems 1
       */
      desde: [string, ...string[]];
      /**
       * @minItems 1
       */
      hacia: [string, ...string[]];
      /**
       * Centro del rótulo de la enzima.
       */
      rotulo: {
        x: number;
        y: number;
      };
      /**
       * Lado de la flecha donde se dibujan los cofactores del paso.
       */
      cofactores: "izquierda" | "derecha" | "arriba" | "abajo";
    }[]
  ];
  /**
   * Región de fondo de cada módulo de la vía.
   */
  modulos: {
    /**
     * ID local de un módulo dentro de su vía (m1, m2, …). El ID global es via:<slug>/m1.
     */
    modulo: string;
    x: number;
    y: number;
    ancho: number;
    alto: number;
  }[];
  /**
   * Rótulos en el borde que llevan a una vía conectada.
   */
  portales: {
    /**
     * ID propio de una vía, por ejemplo via:glucolisis.
     */
    via: string;
    x: number;
    y: number;
  }[];
}

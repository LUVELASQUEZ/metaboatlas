import { Muestra } from "@/components/Muestra";
import type { Seleccion } from "@/components/VistaVia";
import { MARCA_REGULADO } from "@/lib/estilo-evidencia";
import { NOMBRE_ESTADO } from "@/lib/textos";
import type { Cobertura } from "@/lib/tipos/cobertura";
import type { VistaVia } from "@/lib/vista-via";

/** Vista de tabla: equivalente accesible del mapa, con todos los pasos en orden. */
export function TablaPasos({
  vista,
  cobertura,
  onSeleccion,
}: {
  vista: VistaVia;
  cobertura: Cobertura | null;
  onSeleccion: (s: Seleccion) => void;
}) {
  return (
    <section aria-labelledby="titulo-tabla" className="space-y-3">
      <h2 id="titulo-tabla" className="text-2xl font-semibold">
        Pasos de la vía
      </h2>
      {vista.modulos.map((modulo) => (
        <div key={modulo.id} className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm">
            <caption className="py-2 text-left">
              <span className="font-serif text-lg font-semibold">{modulo.nombre}</span>
              {modulo.resumen && <span className="block text-tinta-suave">{modulo.resumen}</span>}
            </caption>
            <thead>
              <tr className="border-b border-borde">
                <th scope="col" className="p-2">
                  N.º
                </th>
                <th scope="col" className="p-2">
                  Paso
                </th>
                <th scope="col" className="p-2">
                  Enzima
                </th>
                <th scope="col" className="p-2">
                  Reacción (Rhea)
                </th>
                {cobertura && (
                  <th scope="col" className="p-2">
                    Evidencia
                  </th>
                )}
              </tr>
            </thead>
            <tbody>
              {vista.pasos
                .filter((p) => p.modulo === modulo.id)
                .map((paso) => {
                  const estado = cobertura?.pasos[paso.id]?.estado;
                  return (
                    <tr key={paso.id} className="border-b border-borde align-top">
                      <td className="p-2">{paso.orden}</td>
                      <th scope="row" className="p-2 font-normal">
                        <button
                          type="button"
                          className="text-left text-primario underline underline-offset-2"
                          onClick={() => onSeleccion({ tipo: "paso", id: paso.id })}
                        >
                          {paso.titulo}
                        </button>
                        {paso.regulacion && (
                          <span className="block text-tinta-suave">
                            <span aria-hidden="true">{MARCA_REGULADO} </span>Paso regulado
                          </span>
                        )}
                      </th>
                      <td className="p-2">
                        {paso.enzimas.map((ec) => (
                          <span key={ec} className="block">
                            <span lang="en">{vista.enzimas[ec]?.nombre}</span>{" "}
                            <span className="font-mono text-xs">{ec.replace("EC:", "EC ")}</span>
                          </span>
                        ))}
                      </td>
                      <td className="p-2" lang="en">
                        {paso.reacciones.map((rid) => (
                          <span key={rid} className="block">
                            {vista.reacciones[rid]?.ecuacion}
                          </span>
                        ))}
                      </td>
                      {cobertura && (
                        <td className="p-2">
                          {estado && (
                            <span className="flex items-center gap-1">
                              <Muestra estado={estado} />
                              {NOMBRE_ESTADO[estado]}
                            </span>
                          )}
                        </td>
                      )}
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      ))}
    </section>
  );
}

import { balanceEnergetico } from "@/lib/balance";
import type { Via } from "@/lib/tipos/via";

/** Tabla de moléculas de energía consumidas y producidas, calculada de la curaduría. */
export function BalanceEnergetico({ via, duplicados = [] }: { via: Via; duplicados?: string[] }) {
  const filas = balanceEnergetico(via.pasos, duplicados);
  const ordenes = duplicados
    .map((id) => via.pasos.find((p) => p.id === id)?.orden)
    .filter((o): o is number => o !== undefined);
  const signo = (n: number) => (n > 0 ? `+${n}` : String(n));
  return (
    <table>
      <caption>
        Por cada molécula de sustrato inicial.
        {ordenes.length > 0 && ` Los pasos ${ordenes.join(", ")} se cuentan dos veces.`}
      </caption>
      <thead>
        <tr>
          <th scope="col">Molécula</th>
          <th scope="col">Consumidas</th>
          <th scope="col">Producidas</th>
          <th scope="col">Balance neto</th>
        </tr>
      </thead>
      <tbody>
        {filas.map((f) => (
          <tr key={f.molecula}>
            <th scope="row">{f.molecula}</th>
            <td>{f.consumidas}</td>
            <td>{f.producidas}</td>
            <td>{signo(f.neto)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

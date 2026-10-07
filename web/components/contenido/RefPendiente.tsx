/** Marca una afirmación que aún espera su referencia bibliográfica (regla 6). */
export function RefPendiente({ nota }: { nota: string }) {
  return (
    <span className="ml-1 rounded-[6px] border border-dashed border-tinta-suave px-1 align-middle text-xs text-tinta-suave">
      referencia pendiente<span className="sr-only">: {nota}</span>
    </span>
  );
}

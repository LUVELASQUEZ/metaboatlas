/** Fórmula química con subíndices reales: C6H12O6 -> C₆H₁₂O₆. */
export function Formula({ formula }: { formula: string }) {
  const partes = formula.split(/(\d+)/).filter(Boolean);
  return (
    <span className="font-mono">
      {partes.map((p, i) => (/^\d+$/.test(p) ? <sub key={i}>{p}</sub> : <span key={i}>{p}</span>))}
    </span>
  );
}

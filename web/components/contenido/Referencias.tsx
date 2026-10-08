import { separarPmids, textoCita } from "@/lib/referencias";
import type { ReferenciaBibliografica } from "@/lib/tipos/referencia";

/** Llamada a una o varias referencias: "[1, 2]", con enlace a la lista. */
export function Ref({ pmid, numeros }: { pmid: string; numeros: Map<string, number> }) {
  const pmids = separarPmids(pmid);
  return (
    <sup className="ml-0.5">
      [
      {pmids.map((p, i) => (
        <span key={p}>
          {i > 0 && ", "}
          <a href={`#ref-${numeros.get(p)}`} aria-label={`Referencia ${numeros.get(p)}`}>
            {numeros.get(p)}
          </a>
        </span>
      ))}
      ]
    </sup>
  );
}

/** Lista numerada de las referencias citadas, con enlaces a DOI, Europe PMC y PMC. */
export function Bibliografia({
  pmids,
  referencias,
  plantillaArticulo,
}: {
  pmids: string[];
  referencias: Record<string, ReferenciaBibliografica | null>;
  plantillaArticulo: string | null;
}) {
  if (pmids.length === 0) return null;
  return (
    <ol className="list-decimal space-y-2 pl-6 text-sm">
      {pmids.map((pmid, i) => {
        const r = referencias[pmid];
        const europePmc = plantillaArticulo?.replace("{id}", pmid);
        return (
          <li key={pmid} id={`ref-${i + 1}`} lang={r ? "en" : undefined}>
            {r ? textoCita(r) : `PMID ${pmid}.`}{" "}
            <span lang="es">
              {r?.doi && (
                <>
                  <a href={`https://doi.org/${r.doi}`}>DOI {r.doi}</a>
                  {" · "}
                </>
              )}
              {europePmc ? <a href={europePmc}>Europe PMC {pmid}</a> : `PMID ${pmid}`}
              {r?.pmcid && <> · lectura gratuita ({r.pmcid})</>}
              {r?.acceso_abierto && <> · acceso abierto</>}
            </span>
          </li>
        );
      })}
    </ol>
  );
}

import type { AnalysisResult } from "@/lib/types";
import { formatDate } from "@/lib/utils";

import { AudienceList } from "./AudienceList";
import { ComparisonTable } from "./ComparisonTable";
import { PriceSummaryCards } from "./PriceSummaryCards";
import { ProductLinks } from "./ProductLinks";
import { ReviewScoreGauge } from "./ReviewScoreGauge";

interface AnalysisViewProps {
  resultado: AnalysisResult;
  pasos: string[];
  filasGuardadas: number;
  errores: string[];
  advertencias: string[];
}

export function AnalysisView({
  resultado,
  pasos,
  filasGuardadas,
  errores,
  advertencias,
}: AnalysisViewProps) {
  const warnings = Array.from(
    new Set([...advertencias, ...resultado.advertencias]),
  );
  const errors = Array.from(new Set([...errores, ...resultado.errores]));

  return (
    <div className="space-y-5">
      <section className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5 dark:border-emerald-900 dark:bg-emerald-950/30">
        <div className="flex items-start gap-3">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-sm font-bold text-white">
            ✓
          </span>
          <div>
            <p className="text-xs font-semibold tracking-wide text-emerald-700 uppercase dark:text-emerald-400">
              Recomendación
            </p>
            <p className="mt-1 text-base font-medium text-emerald-950 dark:text-emerald-50">
              {resultado.recomendacion || "Sin recomendación."}
            </p>
            <p className="mt-2 text-xs text-emerald-800/80 dark:text-emerald-200/80">
              {resultado.producto} · {formatDate(resultado.fecha_consulta)} ·{" "}
              {filasGuardadas} filas guardadas
            </p>
          </div>
        </div>
      </section>

      {resultado.resumen_precios && (
        <PriceSummaryCards summary={resultado.resumen_precios} />
      )}

      <ComparisonTable
        options={resultado.opciones}
        recommended={resultado.resumen_precios?.opcion_recomendada}
        presupuesto={resultado.resumen_precios?.presupuesto}
      />

      {(resultado.resumen_resenas || resultado.usuarios_relevantes) && (
        <div className="grid gap-5 lg:grid-cols-2">
          {resultado.resumen_resenas && (
            <ReviewScoreGauge summary={resultado.resumen_resenas} />
          )}
          {resultado.usuarios_relevantes && (
            <AudienceList summary={resultado.usuarios_relevantes} />
          )}
        </div>
      )}

      {(warnings.length > 0 || errors.length > 0) && (
        <section className="rounded-2xl border border-amber-200 bg-amber-50 p-4 dark:border-amber-900 dark:bg-amber-950/30">
          <h2 className="text-sm font-semibold text-amber-900 dark:text-amber-200">
            Advertencias y errores
          </h2>
          <ul className="mt-2 space-y-1 text-sm text-amber-800 dark:text-amber-200/90">
            {errors.map((error) => (
              <li key={error}>Error: {error}</li>
            ))}
            {warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </section>
      )}

      <ProductLinks options={resultado.opciones} />

      {pasos.length > 0 && (
        <details className="rounded-2xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <summary className="cursor-pointer text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Traza del agente ({pasos.length} pasos)
          </summary>
          <ol className="mt-3 space-y-1 text-xs text-zinc-500 dark:text-zinc-400">
            {pasos.map((paso, index) => (
              <li key={`${paso}-${index}`}>
                {index + 1}. {paso}
              </li>
            ))}
          </ol>
        </details>
      )}
    </div>
  );
}

import type { ReviewSummary } from "@/lib/types";
import { formatScore } from "@/lib/utils";

interface ReviewScoreGaugeProps {
  summary: ReviewSummary;
}

export function ReviewScoreGauge({ summary }: ReviewScoreGaugeProps) {
  const score = Math.max(0, Math.min(10, summary.score));
  const percentage = score * 10;

  return (
    <section className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
      <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
        Reseñas
      </h2>
      <p className="text-xs text-zinc-500 dark:text-zinc-400">
        {summary.resenas_analizadas} reseñas analizadas
      </p>

      <div className="mt-4 flex flex-col gap-5 sm:flex-row sm:items-center">
        <div
          className="relative flex h-28 w-28 shrink-0 items-center justify-center rounded-full"
          style={{
            background: `conic-gradient(#10b981 ${percentage}%, var(--gauge-track) 0)`,
          }}
        >
          <div className="flex h-20 w-20 flex-col items-center justify-center rounded-full bg-white dark:bg-zinc-900">
            <span className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
              {formatScore(score)}
            </span>
            <span className="text-xs text-zinc-500 dark:text-zinc-400">/ 10</span>
          </div>
        </div>
        <p className="text-sm leading-6 text-zinc-600 dark:text-zinc-300">
          {summary.sintesis}
        </p>
      </div>

      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <div>
          <h3 className="text-xs font-semibold tracking-wide text-emerald-700 uppercase dark:text-emerald-400">
            Pros
          </h3>
          <ul className="mt-2 space-y-1 text-sm text-zinc-600 dark:text-zinc-300">
            {summary.pros.length > 0 ? (
              summary.pros.map((pro, index) => (
                <li key={`${pro}-${index}`} className="flex gap-2">
                  <span className="font-semibold text-emerald-600">+</span>
                  {pro}
                </li>
              ))
            ) : (
              <li>Sin datos.</li>
            )}
          </ul>
        </div>
        <div>
          <h3 className="text-xs font-semibold tracking-wide text-rose-700 uppercase dark:text-rose-400">
            Contras
          </h3>
          <ul className="mt-2 space-y-1 text-sm text-zinc-600 dark:text-zinc-300">
            {summary.contras.length > 0 ? (
              summary.contras.map((contra, index) => (
                <li key={`${contra}-${index}`} className="flex gap-2">
                  <span className="font-semibold text-rose-600">−</span>
                  {contra}
                </li>
              ))
            ) : (
              <li>Sin datos.</li>
            )}
          </ul>
        </div>
      </div>

      {summary.fuentes.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-1.5">
          {summary.fuentes.map((fuente, index) => (
            <span
              key={`${fuente}-${index}`}
              className="rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300"
            >
              {fuente}
            </span>
          ))}
        </div>
      )}
    </section>
  );
}

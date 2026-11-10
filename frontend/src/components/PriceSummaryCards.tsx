import type { PriceSummary } from "@/lib/types";
import { formatCurrency } from "@/lib/utils";

interface PriceSummaryCardsProps {
  summary: PriceSummary;
}

export function PriceSummaryCards({ summary }: PriceSummaryCardsProps) {
  const cards = [
    {
      label: "Precio recomendado",
      value: formatCurrency(summary.precio_final, summary.moneda),
      detail: summary.opcion_recomendada,
      accent:
        "border-emerald-200 bg-emerald-50 text-emerald-950 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-50",
    },
    {
      label: "Mínimo",
      value: formatCurrency(summary.precio_minimo, summary.moneda),
      detail: summary.comercio_mas_barato,
      accent:
        "border-sky-200 bg-sky-50 text-sky-950 dark:border-sky-900 dark:bg-sky-950/40 dark:text-sky-50",
    },
    {
      label: "Máximo",
      value: formatCurrency(summary.precio_maximo, summary.moneda),
      detail: summary.comercio_mas_caro,
      accent:
        "border-amber-200 bg-amber-50 text-amber-950 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-50",
    },
    {
      label: "Promedio",
      value: formatCurrency(summary.precio_promedio, summary.moneda),
      detail: `${summary.opciones_consideradas} opciones`,
      accent:
        "border-violet-200 bg-violet-50 text-violet-950 dark:border-violet-900 dark:bg-violet-950/40 dark:text-violet-50",
    },
  ];

  return (
    <section>
      <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
        Resumen de precios
      </h2>
      <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((card) => (
          <div key={card.label} className={`rounded-2xl border p-4 ${card.accent}`}>
            <p className="text-[11px] font-semibold tracking-wide uppercase opacity-70">
              {card.label}
            </p>
            <p className="mt-1 text-2xl font-semibold">{card.value}</p>
            <p className="mt-1 truncate text-xs opacity-70" title={card.detail}>
              {card.detail}
            </p>
          </div>
        ))}
      </div>
      <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
        Rango de {formatCurrency(summary.rango, summary.moneda)} entre{" "}
        {summary.opciones_consideradas} opciones.
      </p>
    </section>
  );
}

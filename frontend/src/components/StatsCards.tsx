import type { Stats } from "@/lib/types";
import { formatCurrency } from "@/lib/utils";

interface StatsCardsProps {
  stats: Stats | null;
  loading: boolean;
}

export function StatsCards({ stats, loading }: StatsCardsProps) {
  if (loading || !stats || stats.total === 0) {
    return null;
  }

  const cards = [
    {
      label: "Consultas",
      value: String(stats.total),
      detail: stats.producto ? `Filtro: ${stats.producto}` : "Todas las consultas",
    },
    {
      label: "Precio mínimo",
      value: formatCurrency(stats.precio_minimo),
      detail: "Mejor precio registrado",
    },
    {
      label: "Precio máximo",
      value: formatCurrency(stats.precio_maximo),
      detail: "Precio más alto",
    },
    {
      label: "Precio promedio",
      value: formatCurrency(stats.precio_promedio),
      detail: "Promedio general",
    },
  ];

  return (
    <section className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((card) => (
          <div
            key={card.label}
            className="rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-900"
          >
            <p className="text-[11px] font-semibold tracking-wide text-zinc-500 uppercase dark:text-zinc-400">
              {card.label}
            </p>
            <p className="mt-1 text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
              {card.value}
            </p>
            <p className="mt-1 truncate text-xs text-zinc-500 dark:text-zinc-400">
              {card.detail}
            </p>
          </div>
        ))}
      </div>

      {stats.por_comercio.length > 0 && (
        <div className="rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
          <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            Promedio por comercio
          </h2>
          <div className="mt-3 grid gap-2 sm:grid-cols-3">
            {stats.por_comercio.map((item) => (
              <div
                key={item.comercio}
                className="flex items-center justify-between gap-3 rounded-xl bg-zinc-50 px-3 py-2 dark:bg-zinc-950"
              >
                <div>
                  <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
                    {item.comercio}
                  </p>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">
                    {item.total} registros
                  </p>
                </div>
                <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                  {formatCurrency(item.precio_promedio)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

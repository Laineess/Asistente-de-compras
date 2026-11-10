import { STORE_LABELS } from "@/lib/constants";
import type { ProductOption } from "@/lib/types";
import { formatCurrency } from "@/lib/utils";

interface ProductLinksProps {
  options: ProductOption[];
}

export function ProductLinks({ options }: ProductLinksProps) {
  const links = Array.from(
    new Map(
      options
        .filter(
          (option): option is ProductOption & { url: string } =>
            Boolean(option.url),
        )
        .map((option) => [option.url, option] as const),
    ).values(),
  );

  return (
    <section className="rounded-2xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
          Enlaces de productos
        </h2>
        <span className="text-xs text-zinc-500 dark:text-zinc-400">
          {links.length} enlaces
        </span>
      </div>

      {links.length === 0 ? (
        <p className="mt-3 text-sm text-zinc-500 dark:text-zinc-400">
          No se encontraron enlaces directos para este análisis.
        </p>
      ) : (
        <ul className="mt-3 divide-y divide-zinc-100 dark:divide-zinc-800">
          {links.map((option) => (
            <li key={option.url}>
              <a
                href={option.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex flex-col gap-1 py-3 text-sm transition hover:text-emerald-700 dark:hover:text-emerald-400 sm:flex-row sm:items-center sm:justify-between"
              >
                <span className="font-medium text-zinc-900 dark:text-zinc-100">
                  {option.nombre}
                </span>
                <span className="text-xs text-zinc-500 dark:text-zinc-400">
                  {STORE_LABELS[option.comercio] ?? option.comercio} ·{" "}
                  {formatCurrency(option.precio, option.moneda)} · Abrir
                </span>
              </a>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

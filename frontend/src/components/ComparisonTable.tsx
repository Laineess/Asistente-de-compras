import { STORE_LABELS } from "@/lib/constants";
import type { ProductOption } from "@/lib/types";
import { formatCurrency } from "@/lib/utils";

interface ComparisonTableProps {
  options: ProductOption[];
  recommended?: string | null;
  presupuesto?: string | number | null;
}

export function ComparisonTable({
  options,
  recommended,
  presupuesto,
}: ComparisonTableProps) {
  if (options.length === 0) {
    return (
      <section>
        <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
          Comparación de opciones
        </h2>
        <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
          No se encontraron opciones para este producto.
        </p>
      </section>
    );
  }

  return (
    <section>
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
          Comparación de opciones
        </h2>
        <span className="text-xs text-zinc-500 dark:text-zinc-400">
          {options.length} opciones
        </span>
      </div>
      <div className="mt-3 overflow-x-auto rounded-2xl border border-zinc-200 dark:border-zinc-800">
        <table className="min-w-full divide-y divide-zinc-200 text-sm dark:divide-zinc-800">
          <thead className="bg-zinc-50 dark:bg-zinc-900">
            <tr>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-semibold tracking-wide text-zinc-500 uppercase dark:text-zinc-400"
              >
                Producto
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-semibold tracking-wide text-zinc-500 uppercase dark:text-zinc-400"
              >
                Tienda
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-semibold tracking-wide text-zinc-500 uppercase dark:text-zinc-400"
              >
                Precio
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-semibold tracking-wide text-zinc-500 uppercase dark:text-zinc-400"
              >
                Calificación
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-semibold tracking-wide text-zinc-500 uppercase dark:text-zinc-400"
              >
                Fuente
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-semibold tracking-wide text-zinc-500 uppercase dark:text-zinc-400"
              >
                Enlace
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
            {options.map((option, index) => {
              const isRecommended = recommended === option.nombre;
              const overBudget =
                presupuesto != null &&
                Number(presupuesto) > 0 &&
                Number(option.precio) > Number(presupuesto);
              return (
                <tr
                  key={`${option.comercio}-${option.nombre}-${index}`}
                  className={
                    isRecommended
                      ? "bg-emerald-50/60 dark:bg-emerald-950/20"
                      : "bg-white dark:bg-zinc-900"
                  }
                >
                  <td className="px-4 py-3 align-top">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium text-zinc-900 dark:text-zinc-100">
                        {option.nombre}
                      </span>
                      {isRecommended && (
                        <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold tracking-wide text-emerald-700 uppercase dark:bg-emerald-900 dark:text-emerald-200">
                          Recomendado
                        </span>
                      )}
                      {overBudget && (
                        <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold tracking-wide text-amber-700 uppercase dark:bg-amber-900 dark:text-amber-200">
                          Sobre presupuesto
                        </span>
                      )}
                    </div>
                    {option.descripcion && (
                      <p className="mt-1 line-clamp-2 max-w-md text-xs text-zinc-500 dark:text-zinc-400">
                        {option.descripcion}
                      </p>
                    )}
                    {option.resenas.length > 0 && (
                      <p className="mt-1 text-xs text-zinc-400 dark:text-zinc-500">
                        {option.resenas.length} reseñas
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-zinc-600 dark:text-zinc-300">
                    {STORE_LABELS[option.comercio] ?? option.comercio}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap font-semibold text-zinc-900 dark:text-zinc-100">
                    {formatCurrency(option.precio, option.moneda)}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-zinc-600 dark:text-zinc-300">
                    {option.calificacion != null
                      ? `${option.calificacion.toFixed(1)} / 5`
                      : "—"}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] font-semibold tracking-wide uppercase ${
                        option.fuente === "tavily"
                          ? "bg-sky-100 text-sky-700 dark:bg-sky-900 dark:text-sky-200"
                          : "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-200"
                      }`}
                    >
                      {option.fuente}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    {option.url ? (
                      <a
                        href={option.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs font-medium text-emerald-700 underline-offset-2 hover:underline dark:text-emerald-400"
                      >
                        Ver
                      </a>
                    ) : (
                      <span className="text-zinc-400 dark:text-zinc-500">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

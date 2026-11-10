import Link from "next/link";

import type { HistoryRow } from "@/lib/types";
import { formatCurrency, formatDate } from "@/lib/utils";

interface HistoryTableProps {
  rows: HistoryRow[];
  loading: boolean;
}

export function HistoryTable({ rows, loading }: HistoryTableProps) {
  if (loading) {
    return (
      <div className="rounded-2xl border border-zinc-200 bg-white p-8 text-center text-sm text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400">
        Cargando historial...
      </div>
    );
  }

  if (rows.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-zinc-300 bg-white p-8 text-center dark:border-zinc-700 dark:bg-zinc-900">
        <p className="text-sm text-zinc-600 dark:text-zinc-300">
          Todavía no hay consultas guardadas.
        </p>
        <Link
          href="/"
          className="mt-3 inline-flex rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700"
        >
          Analizar un producto
        </Link>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-2xl border border-zinc-200 dark:border-zinc-800">
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
              Comercio
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
              Fecha
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
          {rows.map((row) => (
            <tr key={row.id} className="bg-white dark:bg-zinc-900">
              <td className="px-4 py-3 text-zinc-900 dark:text-zinc-100">
                {row.nombre_producto}
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-zinc-600 dark:text-zinc-300">
                {row.comercio}
              </td>
              <td className="px-4 py-3 whitespace-nowrap font-semibold text-zinc-900 dark:text-zinc-100">
                {formatCurrency(row.precio)}
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-zinc-500 dark:text-zinc-400">
                {formatDate(row.fecha_consulta)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { HistoryTable } from "@/components/HistoryTable";
import { StatsCards } from "@/components/StatsCards";
import { fetchHistory, fetchStats } from "@/lib/api";
import type { HistoryRow, Stats } from "@/lib/types";

export default function HistoryPage() {
  const [filtro, setFiltro] = useState("");
  const [producto, setProducto] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const [rows, setRows] = useState<HistoryRow[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [historyData, statsData] = await Promise.all([
          fetchHistory({ limit: 50, producto: producto || undefined }),
          fetchStats(producto || undefined),
        ]);
        if (!cancelled) {
          setRows(historyData);
          setStats(statsData);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "No se pudo cargar el historial.",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [producto, refreshKey]);

  const handleFilter = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setProducto(filtro.trim());
    setRefreshKey((key) => key + 1);
  };

  const handleClear = () => {
    setFiltro("");
    setProducto("");
    setRefreshKey((key) => key + 1);
  };

  const handleRefresh = () => {
    setRefreshKey((key) => key + 1);
  };

  return (
    <div className="space-y-6">
      <section className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold tracking-wide text-emerald-600 uppercase dark:text-emerald-400">
            Historial
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight text-zinc-950 sm:text-3xl dark:text-zinc-50">
            Consultas guardadas
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-zinc-600 dark:text-zinc-400">
            Resultados persistidos en la base de datos. Filtra por producto para
            acotar la búsqueda.
          </p>
        </div>
        <Link
          href="/"
          className="inline-flex items-center justify-center rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-700"
        >
          Nuevo análisis
        </Link>
      </section>

      <form
        onSubmit={handleFilter}
        className="flex flex-col gap-2 rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm sm:flex-row dark:border-zinc-800 dark:bg-zinc-900"
      >
        <label htmlFor="filtro" className="sr-only">
          Producto
        </label>
        <input
          id="filtro"
          value={filtro}
          onChange={(event) => setFiltro(event.target.value)}
          placeholder="Filtrar por producto..."
          className="w-full rounded-xl border border-zinc-200 bg-white px-3 py-2.5 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-50 dark:placeholder:text-zinc-500"
        />
        <div className="flex gap-2">
          <button
            type="submit"
            className="rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-700"
          >
            Filtrar
          </button>
          {(producto || filtro) && (
            <button
              type="button"
              onClick={handleClear}
              className="rounded-xl border border-zinc-200 px-4 py-2.5 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
            >
              Limpiar
            </button>
          )}
          <button
            type="button"
            onClick={handleRefresh}
            disabled={loading}
            className="rounded-xl border border-zinc-200 px-4 py-2.5 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
          >
            Actualizar
          </button>
        </div>
      </form>

      {error && (
        <div
          role="alert"
          className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-200"
        >
          {error}
        </div>
      )}

      <StatsCards stats={stats} loading={loading} />
      <HistoryTable rows={rows} loading={loading} />
    </div>
  );
}

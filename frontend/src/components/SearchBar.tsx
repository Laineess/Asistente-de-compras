"use client";

import type { FormEvent } from "react";

import type { Store } from "@/lib/types";
import { formatCurrency } from "@/lib/utils";

import { StoreSelector } from "./StoreSelector";

interface SearchBarProps {
  producto: string;
  onProductoChange: (value: string) => void;
  tiendas: Store[];
  onToggleTienda: (store: Store) => void;
  limite: number;
  onLimiteChange: (value: number) => void;
  perfil: string;
  onPerfilChange: (value: string) => void;
  presupuesto: number;
  onPresupuestoChange: (value: number) => void;
  usarLlm: boolean;
  onUsarLlmChange: (value: boolean) => void;
  guardar: boolean;
  onGuardarChange: (value: boolean) => void;
  useStream: boolean;
  onUseStreamChange: (value: boolean) => void;
  loading: boolean;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onCancel: () => void;
}

export function SearchBar({
  producto,
  onProductoChange,
  tiendas,
  onToggleTienda,
  limite,
  onLimiteChange,
  perfil,
  onPerfilChange,
  presupuesto,
  onPresupuestoChange,
  usarLlm,
  onUsarLlmChange,
  guardar,
  onGuardarChange,
  useStream,
  onUseStreamChange,
  loading,
  onSubmit,
  onCancel,
}: SearchBarProps) {
  const canSubmit = producto.trim().length > 0 && tiendas.length > 0 && !loading;

  return (
    <form
      onSubmit={onSubmit}
      className="rounded-2xl border border-zinc-200 bg-white p-4 sm:p-6 dark:border-zinc-800 dark:bg-zinc-900"
    >
      <div className="flex flex-col gap-5">
        <div>
          <label
            htmlFor="producto"
            className="text-sm font-medium text-zinc-900 dark:text-zinc-100"
          >
            Producto
          </label>
          <div className="relative mt-2">
            <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-zinc-400">
              <svg
                aria-hidden="true"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className="h-5 w-5"
              >
                <circle cx="11" cy="11" r="7" />
                <path d="m20 20-3.5-3.5" />
              </svg>
            </span>
            <input
              id="producto"
              value={producto}
              onChange={(event) => onProductoChange(event.target.value)}
              disabled={loading}
              placeholder="Ej. laptop, audífonos, cafetera..."
              autoComplete="off"
              className="w-full rounded-xl border border-zinc-200 bg-white py-3 pr-4 pl-10 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-50 dark:placeholder:text-zinc-500"
            />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between gap-3">
            <span className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
              Tiendas
            </span>
            <span className="text-xs text-zinc-500 dark:text-zinc-400">
              {tiendas.length} seleccionadas
            </span>
          </div>
          <div className="mt-2">
            <StoreSelector
              selected={tiendas}
              onToggle={onToggleTienda}
              disabled={loading}
            />
          </div>
          {tiendas.length === 0 && (
            <p className="mt-2 text-xs text-amber-600 dark:text-amber-400">
              Selecciona al menos una tienda para continuar.
            </p>
          )}
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label
              htmlFor="limite"
              className="text-sm font-medium text-zinc-900 dark:text-zinc-100"
            >
              Opciones por tienda
            </label>
            <select
              id="limite"
              value={limite}
              onChange={(event) => onLimiteChange(Number(event.target.value))}
              disabled={loading}
              className="mt-2 w-full rounded-xl border border-zinc-200 bg-white px-3 py-3 text-sm text-zinc-900 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-50"
            >
              {Array.from({ length: 10 }, (_, index) => index + 1).map(
                (value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ),
              )}
            </select>
          </div>
          <div>
            <label
              htmlFor="perfil"
              className="text-sm font-medium text-zinc-900 dark:text-zinc-100"
            >
              Perfil{" "}
              <span className="font-normal text-zinc-500 dark:text-zinc-400">
                (opcional)
              </span>
            </label>
            <input
              id="perfil"
              value={perfil}
              onChange={(event) => onPerfilChange(event.target.value)}
              disabled={loading}
              placeholder="estudiante, gamer, hogar..."
              className="mt-2 w-full rounded-xl border border-zinc-200 bg-white px-3 py-3 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-50 dark:placeholder:text-zinc-500"
            />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between gap-3">
            <label
              htmlFor="presupuesto"
              className="text-sm font-medium text-zinc-900 dark:text-zinc-100"
            >
              Presupuesto máximo
            </label>
            <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
              {presupuesto > 0
                ? formatCurrency(presupuesto, "MXN")
                : "Sin límite"}
            </span>
          </div>
          <input
            id="presupuesto"
            type="range"
            min={0}
            max={100000}
            step={500}
            value={presupuesto}
            onChange={(event) => onPresupuestoChange(Number(event.target.value))}
            disabled={loading}
            className="budget-slider mt-4"
            aria-valuetext={
              presupuesto > 0
                ? formatCurrency(presupuesto, "MXN")
                : "Sin límite"
            }
          />
          <div className="mt-2 flex justify-between text-xs text-zinc-500 dark:text-zinc-400">
            <span>Sin límite</span>
            <span>{formatCurrency(100000, "MXN")}</span>
          </div>
        </div>

        <div className="flex flex-wrap gap-x-6 gap-y-3">
          <label className="flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-300">
            <input
              type="checkbox"
              checked={usarLlm}
              onChange={(event) => onUsarLlmChange(event.target.checked)}
              disabled={loading}
              className="h-4 w-4 rounded border-zinc-300 accent-emerald-600 dark:border-zinc-600"
            />
            Usar Gemini
          </label>
          <label className="flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-300">
            <input
              type="checkbox"
              checked={guardar}
              onChange={(event) => onGuardarChange(event.target.checked)}
              disabled={loading}
              className="h-4 w-4 rounded border-zinc-300 accent-emerald-600 dark:border-zinc-600"
            />
            Guardar en historial
          </label>
          <label className="flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-300">
            <input
              type="checkbox"
              checked={useStream}
              onChange={(event) => onUseStreamChange(event.target.checked)}
              disabled={loading}
              className="h-4 w-4 rounded border-zinc-300 accent-emerald-600 dark:border-zinc-600"
            />
            Progreso en vivo (SSE)
          </label>
        </div>

        <div className="flex flex-col gap-3 border-t border-zinc-100 pt-4 sm:flex-row sm:items-center sm:justify-between dark:border-zinc-800">
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Consejo: desactiva Gemini si agotaste la cuota gratuita.
          </p>
          <div className="flex gap-2">
            {loading && (
              <button
                type="button"
                onClick={onCancel}
                className="rounded-xl border border-zinc-200 px-4 py-2.5 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
              >
                Cancelar
              </button>
            )}
            <button
              type="submit"
              disabled={!canSubmit}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-700 focus:ring-2 focus:ring-emerald-500/40 focus:ring-offset-2 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60 dark:focus:ring-offset-zinc-900"
            >
              {loading ? (
                <>
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                  Analizando...
                </>
              ) : (
                "Analizar precios"
              )}
            </button>
          </div>
        </div>
      </div>
    </form>
  );
}

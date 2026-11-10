"use client";

import { STORES } from "@/lib/constants";
import type { Store } from "@/lib/types";

interface StoreSelectorProps {
  selected: Store[];
  onToggle: (store: Store) => void;
  disabled?: boolean;
}

export function StoreSelector({
  selected,
  onToggle,
  disabled = false,
}: StoreSelectorProps) {
  return (
    <div className="grid gap-2 sm:grid-cols-3">
      {STORES.map((store) => {
        const active = selected.includes(store.value);
        return (
          <button
            key={store.value}
            type="button"
            onClick={() => onToggle(store.value)}
            disabled={disabled}
            aria-pressed={active}
            className={`flex items-center gap-3 rounded-xl border px-3 py-2.5 text-left transition ${
              active
                ? "border-emerald-500 bg-emerald-50 text-emerald-950 dark:border-emerald-500 dark:bg-emerald-950/40 dark:text-emerald-50"
                : "border-zinc-200 bg-white text-zinc-700 hover:border-zinc-300 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:border-zinc-700"
            } ${disabled ? "cursor-not-allowed opacity-60" : ""}`}
          >
            <span
              className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                active
                  ? "bg-emerald-600 text-white"
                  : "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400"
              }`}
            >
              {active ? "✓" : store.label.charAt(0)}
            </span>
            <span className="flex flex-col">
              <span className="text-sm font-medium">{store.label}</span>
              <span className="text-xs text-zinc-500 dark:text-zinc-400">
                {store.hint}
              </span>
            </span>
          </button>
        );
      })}
    </div>
  );
}

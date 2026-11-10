import { NODE_LABELS, NODE_ORDER } from "@/lib/constants";

interface AgentProgressProps {
  nodos: string[];
  pasos: string[];
  loading: boolean;
}

export function AgentProgress({
  nodos,
  pasos,
  loading,
}: AgentProgressProps) {
  const seen = new Set(nodos);
  const activeNode = loading && nodos.length > 0 ? nodos[nodos.length - 1] : null;

  return (
    <section
      aria-live="polite"
      className="rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm sm:p-6 dark:border-zinc-800 dark:bg-zinc-900"
    >
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            Progreso del agente
          </h2>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            {loading ? "Trabajando..." : "Ejecución completada"}
          </p>
        </div>
        {loading && (
          <span className="h-5 w-5 animate-spin rounded-full border-2 border-emerald-500/30 border-t-emerald-500" />
        )}
      </div>

      <ol className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        {NODE_ORDER.map((node) => {
          const done = seen.has(node);
          const active = activeNode === node;
          return (
            <li
              key={node}
              className={`flex items-center gap-2 rounded-xl border px-3 py-2 text-xs font-medium ${
                active
                  ? "border-sky-200 bg-sky-50 text-sky-800 dark:border-sky-900 dark:bg-sky-950/40 dark:text-sky-200"
                  : done
                    ? "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200"
                    : "border-zinc-200 bg-zinc-50 text-zinc-500 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-500"
              }`}
            >
              <span
                className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] ${
                  active
                    ? "bg-sky-100 text-sky-700 dark:bg-sky-900 dark:text-sky-200"
                    : done
                      ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-200"
                      : "bg-zinc-100 text-zinc-400 dark:bg-zinc-800 dark:text-zinc-500"
                }`}
              >
                {active ? (
                  <span className="h-3 w-3 animate-spin rounded-full border-2 border-sky-500/30 border-t-sky-500" />
                ) : done ? (
                  "✓"
                ) : (
                  "•"
                )}
              </span>
              {NODE_LABELS[node] ?? node}
            </li>
          );
        })}
      </ol>

      {pasos.length > 0 && (
        <details className="mt-4 rounded-xl border border-zinc-100 bg-zinc-50 p-3 dark:border-zinc-800 dark:bg-zinc-950">
          <summary className="cursor-pointer text-xs font-medium text-zinc-600 dark:text-zinc-400">
            Traza ({pasos.length} pasos)
          </summary>
          <ol className="mt-2 space-y-1 text-xs text-zinc-500 dark:text-zinc-400">
            {pasos.map((paso, index) => (
              <li key={`${paso}-${index}`}>
                {index + 1}. {paso}
              </li>
            ))}
          </ol>
        </details>
      )}
    </section>
  );
}

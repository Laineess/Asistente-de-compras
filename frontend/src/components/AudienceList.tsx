import type { AudienceSummary } from "@/lib/types";

interface AudienceListProps {
  summary: AudienceSummary;
}

export function AudienceList({ summary }: AudienceListProps) {
  return (
    <section className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
      <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
        Perfiles de comprador
      </h2>
      {summary.sintesis && (
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          {summary.sintesis}
        </p>
      )}

      <div className="mt-4 space-y-3">
        {summary.perfiles.length === 0 ? (
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            No se identificaron perfiles.
          </p>
        ) : (
          summary.perfiles.map((profile, index) => {
            const percentage =
              profile.porcentaje == null
                ? null
                : Math.max(0, Math.min(100, profile.porcentaje));
            return (
              <div
                key={`${profile.perfil}-${index}`}
                className="rounded-xl border border-zinc-100 bg-zinc-50 p-4 dark:border-zinc-800 dark:bg-zinc-950"
              >
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                    {profile.perfil}
                  </h3>
                  {percentage != null && (
                    <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold text-emerald-700 dark:bg-emerald-900 dark:text-emerald-200">
                      {Math.round(percentage)}%
                    </span>
                  )}
                </div>
                <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-300">
                  {profile.descripcion}
                </p>
                {profile.evidencia && (
                  <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
                    Evidencia: {profile.evidencia}
                  </p>
                )}
                {percentage != null && (
                  <div className="mt-3 h-2 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
                    <div
                      className="h-full rounded-full bg-emerald-500"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function toStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string");
}

export function extractPasos(data: Record<string, unknown>): string[] {
  for (const value of Object.values(data)) {
    if (isRecord(value) && Array.isArray(value.pasos)) {
      const pasos = toStringArray(value.pasos);
      if (pasos.length > 0) {
        return pasos;
      }
    }
  }
  return [];
}

export function formatCurrency(
  value: string | number | null | undefined,
  currency = "MXN",
): string {
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  const numeric = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numeric)) {
    return "—";
  }
  try {
    return new Intl.NumberFormat("es-MX", {
      style: "currency",
      currency,
      maximumFractionDigits: 2,
    }).format(numeric);
  } catch {
    return `${numeric.toFixed(2)} ${currency}`;
  }
}

export function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "—";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("es-MX", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function formatScore(value: number): string {
  return Number.isFinite(value) ? value.toFixed(1) : "—";
}

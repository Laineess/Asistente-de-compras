import type {
  AnalysisResult,
  AnalyzeRequest,
  AnalyzeResponse,
  HistoryRow,
  Stats,
  StreamDonePayload,
} from "./types";
import { isRecord, toStringArray } from "./utils";

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

export interface StreamHandlers {
  onUpdate?: (nodos: string[], data: Record<string, unknown>) => void;
  onDone?: (payload: StreamDonePayload) => void;
  onError?: (mensaje: string) => void;
  signal?: AbortSignal;
}

async function readError(response: Response): Promise<string> {
  const fallback = `Error HTTP ${response.status}`;
  try {
    const data: unknown = await response.json();
    if (!isRecord(data)) {
      return fallback;
    }
    const detail = data.detail;
    if (typeof detail === "string") {
      return detail;
    }
    if (isRecord(detail)) {
      const mensaje =
        typeof detail.mensaje === "string" ? detail.mensaje : fallback;
      const errores = toStringArray(detail.errores);
      return errores.length > 0 ? `${mensaje}: ${errores.join("; ")}` : mensaje;
    }
    return fallback;
  } catch {
    return fallback;
  }
}

async function request<T>(
  path: string,
  init?: RequestInit,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, signal });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return (await response.json()) as T;
}

export function analyze(
  payload: AnalyzeRequest,
  signal?: AbortSignal,
): Promise<AnalyzeResponse> {
  return request<AnalyzeResponse>(
    "/api/analyze",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
    signal,
  );
}

export function fetchHistory(
  options: { limit?: number; producto?: string } = {},
  signal?: AbortSignal,
): Promise<HistoryRow[]> {
  const params = new URLSearchParams({
    limit: String(options.limit ?? 50),
  });
  if (options.producto) {
    params.set("producto", options.producto);
  }
  return request<HistoryRow[]>(
    `/api/history?${params.toString()}`,
    { cache: "no-store" },
    signal,
  );
}

export function fetchStats(
  producto?: string,
  signal?: AbortSignal,
): Promise<Stats> {
  const params = new URLSearchParams();
  if (producto) {
    params.set("producto", producto);
  }
  const query = params.toString();
  return request<Stats>(
    `/api/stats${query ? `?${query}` : ""}`,
    { cache: "no-store" },
    signal,
  );
}

function parseDone(payload: Record<string, unknown>): StreamDonePayload {
  const resultado =
    payload.resultado === null
      ? null
      : isRecord(payload.resultado)
        ? (payload.resultado as unknown as AnalysisResult)
        : null;

  return {
    event: "done",
    resultado,
    pasos: toStringArray(payload.pasos),
    errores: toStringArray(payload.errores),
    advertencias: toStringArray(payload.advertencias),
    filas_guardadas:
      typeof payload.filas_guardadas === "number"
        ? payload.filas_guardadas
        : 0,
  };
}

export async function analyzeStream(
  payload: AnalyzeRequest,
  handlers: StreamHandlers = {},
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/analyze/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify(payload),
    signal: handlers.signal,
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }
  if (!response.body) {
    throw new Error("El navegador no soporta streaming.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const dispatch = (raw: string) => {
    const dataLines = raw
      .split("\n")
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice(5).trimStart());
    if (dataLines.length === 0) {
      return;
    }

    let parsed: unknown;
    try {
      parsed = JSON.parse(dataLines.join("\n"));
    } catch {
      return;
    }
    if (!isRecord(parsed) || typeof parsed.event !== "string") {
      return;
    }

    if (parsed.event === "update") {
      const nodos = toStringArray(parsed.nodos);
      const data = isRecord(parsed.data) ? parsed.data : {};
      handlers.onUpdate?.(nodos, data);
      return;
    }
    if (parsed.event === "done") {
      handlers.onDone?.(parseDone(parsed));
      return;
    }
    if (parsed.event === "error") {
      handlers.onError?.(
        typeof parsed.mensaje === "string"
          ? parsed.mensaje
          : "Error en el stream del agente.",
      );
    }
  };

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
      let boundary = buffer.indexOf("\n\n");
      while (boundary !== -1) {
        const chunk = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        dispatch(chunk);
        boundary = buffer.indexOf("\n\n");
      }
    }
    buffer += decoder.decode();
    if (buffer.trim()) {
      dispatch(buffer);
    }
  } finally {
    reader.releaseLock();
  }
}

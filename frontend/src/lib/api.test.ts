import { afterEach, describe, expect, it, vi } from "vitest";

import { analyzeStream, fetchHistory, fetchStats } from "./api";
import type { AnalyzeRequest } from "./types";

const request: AnalyzeRequest = {
  producto: "laptop",
  tiendas: ["walmart", "costco"],
  limite_por_tienda: 2,
  perfil: null,
  usar_llm: false,
  guardar: false,
};

function sseResponse(chunks: string[]): Response {
  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });
  return new Response(stream, {
    status: 200,
    headers: { "Content-Type": "text/event-stream" },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("analyzeStream", () => {
  it("emits update and done events across chunk boundaries", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      sseResponse([
        'data: {"event":"up',
        'date","nodos":["buscar"],"data":{"buscar":{"pasos":["buscador:3 opciones"]}}}\n\n',
        'data: {"event":"done","resultado":null,"pasos":["validar:ok"],',
        '"errores":["sin resultado"],"advertencias":["mock"],"filas_guardadas":0}\n\n',
      ]),
    );
    vi.stubGlobal("fetch", fetchMock);
    const onUpdate = vi.fn();
    const onDone = vi.fn();

    await analyzeStream(request, { onUpdate, onDone });

    expect(onUpdate).toHaveBeenCalledWith(["buscar"], {
      buscar: { pasos: ["buscador:3 opciones"] },
    });
    expect(onDone).toHaveBeenCalledWith({
      event: "done",
      resultado: null,
      pasos: ["validar:ok"],
      errores: ["sin resultado"],
      advertencias: ["mock"],
      filas_guardadas: 0,
    });

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/analyze/stream");
    expect(init.method).toBe("POST");
    expect(init.body).toBe(JSON.stringify(request));
  });

  it("forwards error events", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        sseResponse(['data: {"event":"error","mensaje":"fallo del agente"}\n\n']),
      ),
    );
    const onError = vi.fn();

    await analyzeStream(request, { onError });

    expect(onError).toHaveBeenCalledWith("fallo del agente");
  });

  it("throws a readable error when the API rejects the request", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            detail: { mensaje: "No se pudo", errores: ["a", "b"] },
          }),
          {
            status: 502,
            headers: { "Content-Type": "application/json" },
          },
        ),
      ),
    );

    await expect(analyzeStream(request)).rejects.toThrow("No se pudo: a; b");
  });
});

describe("history and stats requests", () => {
  it("builds query strings and returns parsed JSON", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify([
            {
              id: 1,
              nombre_producto: "Laptop",
              comercio: "Walmart",
              precio: "12000.00",
              fecha_consulta: "2026-11-08T12:00:00",
            },
          ]),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            producto: "laptop",
            total: 1,
            precio_minimo: "12000.00",
            precio_maximo: "12000.00",
            precio_promedio: "12000.00",
            por_comercio: [],
          }),
          { status: 200 },
        ),
      );
    vi.stubGlobal("fetch", fetchMock);

    const rows = await fetchHistory({ limit: 10, producto: "laptop" });
    const stats = await fetchStats("laptop");

    expect(rows[0].nombre_producto).toBe("Laptop");
    expect(stats.total).toBe(1);
    expect(fetchMock.mock.calls[0][0]).toContain(
      "/api/history?limit=10&producto=laptop",
    );
    expect(fetchMock.mock.calls[1][0]).toContain("/api/stats?producto=laptop");
  });
});

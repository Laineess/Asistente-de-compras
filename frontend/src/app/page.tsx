"use client";

import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";

import { AgentProgress } from "@/components/AgentProgress";
import { AnalysisView } from "@/components/AnalysisView";
import { SearchBar } from "@/components/SearchBar";
import { analyze, analyzeStream } from "@/lib/api";
import { STORE_ORDER } from "@/lib/constants";
import type { AnalyzeRequest, AnalyzeResponse, Store } from "@/lib/types";
import { extractPasos } from "@/lib/utils";

type Status = "idle" | "loading" | "done" | "error";

const FEATURES = [
  {
    step: "01",
    title: "Precios comparados",
    description:
      "Mínimo, máximo y promedio por tienda, con la opción recomendada.",
  },
  {
    step: "02",
    title: "Reseñas y perfiles",
    description:
      "Análisis de opiniones y perfiles de comprador según tu consulta.",
  },
  {
    step: "03",
    title: "Historial persistente",
    description:
      "Cada opción analizada se guarda para consultarla después.",
  },
];

export default function Home() {
  const [producto, setProducto] = useState("");
  const [tiendas, setTiendas] = useState<Store[]>(() => [...STORE_ORDER]);
  const [limite, setLimite] = useState(3);
  const [perfil, setPerfil] = useState("");
  const [presupuesto, setPresupuesto] = useState(0);
  const [usarLlm, setUsarLlm] = useState(true);
  const [guardar, setGuardar] = useState(true);
  const [useStream, setUseStream] = useState(true);
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [nodos, setNodos] = useState<string[]>([]);
  const [pasos, setPasos] = useState<string[]>([]);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const loading = status === "loading";

  const handleToggleTienda = (store: Store) => {
    setTiendas((current) =>
      current.includes(store)
        ? current.filter((item) => item !== store)
        : [...current, store],
    );
  };

  const handleCancel = () => {
    abortRef.current?.abort();
    setStatus("idle");
    setError(null);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const consulta = producto.trim();
    if (!consulta) {
      setError("Escribe un producto para analizar.");
      return;
    }
    if (tiendas.length === 0) {
      setError("Selecciona al menos una tienda.");
      return;
    }

    const payload: AnalyzeRequest = {
      producto: consulta,
      tiendas,
      limite_por_tienda: limite,
      perfil: perfil.trim() || null,
      presupuesto: presupuesto > 0 ? presupuesto : null,
      usar_llm: usarLlm,
      guardar,
    };

    setStatus("loading");
    setError(null);
    setResult(null);
    setNodos([]);
    setPasos([]);

    const controller = new AbortController();
    abortRef.current = controller;
    let completed = false;

    try {
      if (useStream) {
        await analyzeStream(payload, {
          signal: controller.signal,
          onUpdate: (nodosActuales, data) => {
            setNodos((current) =>
              Array.from(new Set([...current, ...nodosActuales])),
            );
            const latest = extractPasos(data);
            if (latest.length > 0) {
              setPasos(latest);
            }
          },
          onDone: (done) => {
            completed = true;
            setPasos(done.pasos);
            if (done.resultado) {
              setResult({
                resultado: done.resultado,
                pasos: done.pasos,
                errores: done.errores,
                advertencias: done.advertencias,
                filas_guardadas: done.filas_guardadas,
              });
              setStatus("done");
            } else {
              setError(
                done.errores.length > 0
                  ? done.errores.join("; ")
                  : "El agente no generó un resultado.",
              );
              setStatus("error");
            }
          },
          onError: (mensaje) => {
            completed = true;
            setError(mensaje);
            setStatus("error");
          },
        });

        if (!completed && !controller.signal.aborted) {
          setError("El stream terminó sin un resultado.");
          setStatus("error");
        }
      } else {
        const response = await analyze(payload, controller.signal);
        setResult(response);
        setPasos(response.pasos);
        setStatus("done");
      }
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        setStatus("idle");
        setError(null);
      } else {
        setStatus("error");
        setError(
          err instanceof Error ? err.message : "Ocurrió un error inesperado.",
        );
      }
    } finally {
      abortRef.current = null;
    }
  };

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-zinc-200 bg-white p-6 sm:p-8 dark:border-zinc-800 dark:bg-zinc-900">
        <div className="max-w-3xl">
          <p className="text-xs font-semibold tracking-wide text-emerald-600 uppercase dark:text-emerald-400">
            Agente multiagente
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-zinc-950 sm:text-4xl dark:text-zinc-50">
            Decide tu próxima compra con datos
          </h1>
          <p className="mt-3 text-sm leading-6 text-zinc-600 sm:text-base dark:text-zinc-400">
            Compara precios y reseñas en Walmart, Costco y Sam&apos;s. El agente
            busca, analiza opiniones, identifica perfiles y guarda el resultado.
          </p>
        </div>
      </section>

      <SearchBar
        producto={producto}
        onProductoChange={setProducto}
        tiendas={tiendas}
        onToggleTienda={handleToggleTienda}
        limite={limite}
        onLimiteChange={setLimite}
        perfil={perfil}
        onPerfilChange={setPerfil}
        presupuesto={presupuesto}
        onPresupuestoChange={setPresupuesto}
        usarLlm={usarLlm}
        onUsarLlmChange={setUsarLlm}
        guardar={guardar}
        onGuardarChange={setGuardar}
        useStream={useStream}
        onUseStreamChange={setUseStream}
        loading={loading}
        onSubmit={handleSubmit}
        onCancel={handleCancel}
      />

      {error && (
        <div
          role="alert"
          className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-200"
        >
          {error}
        </div>
      )}

      {(loading || nodos.length > 0) && (
        <AgentProgress nodos={nodos} pasos={pasos} loading={loading} />
      )}

      {result && (
        <AnalysisView
          resultado={result.resultado}
          pasos={result.pasos}
          filasGuardadas={result.filas_guardadas}
          errores={result.errores}
          advertencias={result.advertencias}
        />
      )}

      {!result && !loading && !error && (
        <section className="grid gap-3 sm:grid-cols-3">
          {FEATURES.map((feature) => (
            <div
              key={feature.step}
              className="rounded-2xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900"
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100 text-xs font-bold text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
                {feature.step}
              </span>
              <h2 className="mt-3 text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                {feature.title}
              </h2>
              <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
                {feature.description}
              </p>
            </div>
          ))}
        </section>
      )}
    </div>
  );
}

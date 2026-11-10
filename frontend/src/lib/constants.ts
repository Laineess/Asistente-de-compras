import type { Store } from "./types";

export const STORES: ReadonlyArray<{
  value: Store;
  label: string;
  hint: string;
}> = [
  { value: "walmart", label: "Walmart", hint: "Precios bajos" },
  { value: "costco", label: "Costco", hint: "Mayoreo" },
  { value: "sams", label: "Sam's", hint: "Membresía" },
];

export const STORE_ORDER: Store[] = ["walmart", "costco", "sams"];

export const STORE_LABELS: Record<Store, string> = {
  walmart: "Walmart",
  costco: "Costco",
  sams: "Sam's",
};

export const NODE_ORDER: string[] = [
  "supervisor",
  "buscar",
  "precios",
  "resenas",
  "audiencia",
  "sintetizar",
  "validar",
  "persistir",
];

export const NODE_LABELS: Record<string, string> = {
  supervisor: "Supervisor",
  buscar: "Buscador",
  precios: "Precios",
  resenas: "Reseñas",
  audiencia: "Audiencia",
  sintetizar: "Síntesis",
  validar: "Validación",
  persistir: "Persistencia",
};

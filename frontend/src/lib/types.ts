export type Store = "walmart" | "costco" | "sams";

export type Source = "tavily" | "mock";

export interface ReviewSnippet {
  autor?: string | null;
  texto: string;
  calificacion?: number | null;
}

export interface ProductOption {
  nombre: string;
  comercio: Store;
  precio: string | number;
  moneda: string;
  url?: string | null;
  descripcion?: string | null;
  calificacion?: number | null;
  resenas: ReviewSnippet[];
  fuente: Source;
}

export interface PriceSummary {
  precio_final: string | number;
  opcion_recomendada: string;
  precio_promedio: string | number;
  precio_minimo: string | number;
  precio_maximo: string | number;
  rango: string | number;
  moneda: string;
  opciones_consideradas: number;
  comercio_mas_barato: string;
  comercio_mas_caro: string;
  presupuesto?: string | number | null;
  opciones_dentro_presupuesto?: number | null;
}

export interface ReviewSummary {
  score: number;
  resenas_analizadas: number;
  sintesis: string;
  pros: string[];
  contras: string[];
  fuentes: string[];
}

export interface AudienceProfile {
  perfil: string;
  descripcion: string;
  evidencia?: string | null;
  porcentaje?: number | null;
}

export interface AudienceSummary {
  perfiles: AudienceProfile[];
  sintesis?: string | null;
}

export interface AnalysisResult {
  producto: string;
  tiendas: Store[];
  opciones: ProductOption[];
  resumen_precios?: PriceSummary | null;
  resumen_resenas?: ReviewSummary | null;
  usuarios_relevantes?: AudienceSummary | null;
  presupuesto?: string | number | null;
  recomendacion: string;
  advertencias: string[];
  filas_guardadas: number;
  errores: string[];
  fecha_consulta: string;
}

export interface AnalyzeRequest {
  producto: string;
  tiendas: Store[];
  limite_por_tienda: number;
  perfil?: string | null;
  presupuesto?: number | null;
  usar_llm: boolean;
  guardar: boolean;
}

export interface AnalyzeResponse {
  resultado: AnalysisResult;
  pasos: string[];
  errores: string[];
  advertencias: string[];
  filas_guardadas: number;
}

export interface StreamDonePayload {
  event: "done";
  resultado: AnalysisResult | null;
  pasos: string[];
  errores: string[];
  advertencias: string[];
  filas_guardadas: number;
}

export interface HistoryRow {
  id: number;
  nombre_producto: string;
  comercio: string;
  precio: string;
  fecha_consulta: string;
}

export interface ComercioStats {
  comercio: string;
  total: number;
  precio_promedio: string | null;
}

export interface Stats {
  producto?: string | null;
  total: number;
  precio_minimo: string | null;
  precio_maximo: string | null;
  precio_promedio: string | null;
  por_comercio: ComercioStats[];
}

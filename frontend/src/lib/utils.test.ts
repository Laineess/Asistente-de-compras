import { describe, expect, it } from "vitest";

import {
  extractPasos,
  formatCurrency,
  formatDate,
  formatScore,
  isRecord,
  toStringArray,
} from "./utils";

describe("isRecord", () => {
  it("accepts plain objects and rejects null, arrays and primitives", () => {
    expect(isRecord({})).toBe(true);
    expect(isRecord({ pasos: [] })).toBe(true);
    expect(isRecord(null)).toBe(false);
    expect(isRecord([])).toBe(false);
    expect(isRecord("texto")).toBe(false);
    expect(isRecord(42)).toBe(false);
  });
});

describe("toStringArray", () => {
  it("keeps only string values from arrays", () => {
    expect(toStringArray(["a", 1, null, "b"])).toEqual(["a", "b"]);
    expect(toStringArray("a")).toEqual([]);
    expect(toStringArray(null)).toEqual([]);
  });
});

describe("extractPasos", () => {
  it("returns the first non-empty pasos array found in the event data", () => {
    const data = {
      supervisor: { pasos: [] },
      buscar: { pasos: ["buscador:3 opciones", 1, "buscar:ok"] },
      precios: { pasos: ["precios:ok"] },
    };

    expect(extractPasos(data)).toEqual(["buscador:3 opciones", "buscar:ok"]);
    expect(extractPasos({})).toEqual([]);
  });
});

describe("formatCurrency", () => {
  it("formats valid amounts and handles empty values", () => {
    expect(formatCurrency("12000.50")).toContain("12,000.50");
    expect(formatCurrency(12000)).toContain("12,000.00");
    expect(formatCurrency(null)).toBe("—");
    expect(formatCurrency("")).toBe("—");
    expect(formatCurrency("no-es-numero")).toBe("—");
  });

  it("falls back when the currency code is invalid", () => {
    expect(formatCurrency(10, "INVALID")).toBe("10.00 INVALID");
  });
});

describe("formatDate", () => {
  it("formats valid dates and preserves invalid input", () => {
    expect(formatDate("2026-11-08T12:00:00")).toContain("2026");
    expect(formatDate("fecha-invalida")).toBe("fecha-invalida");
    expect(formatDate(null)).toBe("—");
  });
});

describe("formatScore", () => {
  it("rounds scores to one decimal and handles non-finite values", () => {
    expect(formatScore(7.5)).toBe("7.5");
    expect(formatScore(7.55)).toBe("7.5");
    expect(formatScore(Number.NaN)).toBe("—");
  });
});

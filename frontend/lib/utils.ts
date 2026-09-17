import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Safely converts an unknown value (number, numeric string, etc.) to a JavaScript number.
 * Returns null if the value is null, undefined, empty string, NaN, or non-finite.
 */
export function toNumber(value: unknown): number | null {
  if (value === null || value === undefined) return null;
  if (typeof value === "string" && value.trim() === "") return null;
  const num = typeof value === "number" ? value : Number(value);
  if (isNaN(num) || !isFinite(num)) return null;
  return num;
}

export function formatIndex(value: unknown): string {
  const num = toNumber(value);
  if (num === null) return "N/A";
  return num.toFixed(1);
}

export function formatPercent(value: unknown, includeSign = true): string {
  const num = toNumber(value);
  if (num === null) return "N/A";
  const formatted = Math.abs(num).toFixed(1) + "%";
  if (!includeSign) return formatted;
  return num > 0 ? `+${formatted}` : num < 0 ? `-${formatted}` : formatted;
}

export function formatNumber(value: unknown, decimals = 2): string {
  const num = toNumber(value);
  if (num === null) return "N/A";
  return num.toFixed(decimals);
}

export function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}

export function formatDateTime(dateTimeStr: string): string {
  try {
    const d = new Date(dateTimeStr);
    if (isNaN(d.getTime())) return dateTimeStr;
    return d.toLocaleTimeString("en-IN", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    }) + ", " + d.toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
    });
  } catch {
    return dateTimeStr;
  }
}

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Chart data metrics utilities
export interface ChartMetrics {
  total: number;
  change: number;
  changePercent: number;
  growthRate: number;
  trend: "up" | "down" | "stable";
}

export function calculateChartMetrics(
  data: Array<{ year: number; [key: string]: number }>
): ChartMetrics | null {
  if (!data || data.length === 0) return null;

  const sortedData = [...data].sort((a, b) => a.year - b.year);
  const firstValue =
    Object.values(sortedData[0]).find(
      (v) => typeof v === "number" && v !== sortedData[0].year
    ) || 0;
  const lastValue =
    Object.values(sortedData[sortedData.length - 1]).find(
      (v) =>
        typeof v === "number" && v !== sortedData[sortedData.length - 1].year
    ) || 0;

  const change = lastValue - firstValue;
  const changePercent = firstValue !== 0 ? (change / firstValue) * 100 : 0;
  const years = sortedData[sortedData.length - 1].year - sortedData[0].year;
  const growthRate = years > 0 ? changePercent / years : 0;

  let trend: "up" | "down" | "stable" = "stable";
  if (changePercent > 1) trend = "up";
  else if (changePercent < -1) trend = "down";

  return {
    total: lastValue,
    change,
    changePercent,
    growthRate,
    trend,
  };
}

export function formatNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toFixed(0);
}

export function formatPercent(num: number): string {
  const sign = num >= 0 ? "+" : "";
  return `${sign}${num.toFixed(1)}%`;
}

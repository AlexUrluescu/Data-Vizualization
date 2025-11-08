"use client";

import * as React from "react";
import { BarChart, Bar, CartesianGrid, XAxis, YAxis, ResponsiveContainer } from "recharts";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ChartConfig,
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { PollutionData } from "./chart-pollution-trends";

interface IChartPollutionBar {
  pollutionData: PollutionData[];
  title?: string;
}

const chartConfig = {
  value: {
    label: "Value",
    color: "#3b82f6",
  },
} satisfies ChartConfig;

export default function ChartPollutionBar({
  pollutionData,
  title = "Latest Pollution Levels",
}: IChartPollutionBar) {
  const barData = React.useMemo(() => {
    if (pollutionData.length === 0) return [];

    // Get latest year data
    const latest = pollutionData[pollutionData.length - 1];
    const previous = pollutionData.length > 1 ? pollutionData[pollutionData.length - 2] : null;

    // Convert to bar chart format
    const metrics = Object.keys(latest).filter(key => key !== 'year' && key !== '_id' && key !== 'cityId');

    return metrics.map(metric => {
      const currentValue = latest[metric] || 0;
      const previousValue = previous ? (previous[metric] || 0) : 0;
      const change = previousValue !== 0 ? ((currentValue - previousValue) / previousValue) * 100 : 0;
      const trend = change > 1 ? 'up' : change < -1 ? 'down' : 'stable';

      // Color based on pollution level (assuming higher = worse)
      let fill = "#10b981"; // green (good)
      if (currentValue > 75) fill = "#ef4444"; // red (bad)
      else if (currentValue > 50) fill = "#f59e0b"; // orange (moderate)
      else if (currentValue > 25) fill = "#f97316"; // yellow (fair)

      return {
        metric: metric.toUpperCase(),
        value: currentValue,
        fill,
        change,
        trend,
      };
    });
  }, [pollutionData]);

  const latestYear = pollutionData.length > 0 ? pollutionData[pollutionData.length - 1].year : new Date().getFullYear();

  return (
    <Card className="pt-0 transition-all duration-300 hover:shadow-lg">
      <CardHeader className="flex items-center gap-2 space-y-0 border-b py-5">
        <div className="grid flex-1 gap-1">
          <CardTitle>{title}</CardTitle>
          <CardDescription>
            Current pollution metrics for {latestYear}
          </CardDescription>
        </div>
      </CardHeader>

      {/* Metrics Overview */}
      <div className="px-4 py-4 bg-muted/50 border-b sm:px-6">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {barData.slice(0, 4).map((item) => {
            const TrendIcon = item.trend === 'up' ? TrendingUp : item.trend === 'down' ? TrendingDown : Minus;
            return (
              <div key={item.metric} className="space-y-1 min-w-0">
                <p className="text-xs text-muted-foreground font-medium truncate">{item.metric}</p>
                <div className="flex items-center gap-2">
                  <p className="text-xl font-bold sm:text-2xl">{item.value.toFixed(1)}</p>
                  {item.change !== 0 && (
                    <div className={`flex items-center text-xs font-semibold ${
                      item.trend === 'up' ? 'text-red-600' :
                      item.trend === 'down' ? 'text-green-600' : 'text-gray-600'
                    }`}>
                      <TrendIcon className="h-3 w-3" />
                      <span>{Math.abs(item.change).toFixed(1)}%</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <CardContent className="px-2 pt-4 sm:px-6 sm:pt-6">
        <ChartContainer
          config={chartConfig}
          className="aspect-auto h-[300px] w-full"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="metric"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
              />
              <YAxis
                tickLine={false}
                axisLine={false}
                tickMargin={8}
              />
              <ChartTooltip
                content={
                  <ChartTooltipContent
                    formatter={(value, name) => [
                      `${(value as number).toFixed(2)}`,
                      name as string
                    ]}
                  />
                }
              />
              <Bar
                dataKey="value"
                radius={[8, 8, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>

        {/* Legend for colors */}
        <div className="mt-4 flex flex-wrap gap-4 justify-center text-xs">
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded" style={{ backgroundColor: "#10b981" }} />
            <span className="text-muted-foreground">Good (0-25)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded" style={{ backgroundColor: "#f97316" }} />
            <span className="text-muted-foreground">Fair (25-50)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded" style={{ backgroundColor: "#f59e0b" }} />
            <span className="text-muted-foreground">Moderate (50-75)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded" style={{ backgroundColor: "#ef4444" }} />
            <span className="text-muted-foreground">Poor (75+)</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

"use client";

import * as React from "react";
import { LineChart, Line, CartesianGrid, XAxis, YAxis, ResponsiveContainer } from "recharts";

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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export type PollutionData = {
  year: number;
  [key: string]: number; // Dynamic pollution metrics
};

interface IChartPollutionTrends {
  pollutionData: PollutionData[];
  title?: string;
}

const chartConfig = {
  pm25: {
    label: "PM2.5",
    color: "#ef4444",
  },
  pm10: {
    label: "PM10",
    color: "#f97316",
  },
  no2: {
    label: "NO2",
    color: "#3b82f6",
  },
  so2: {
    label: "SO2",
    color: "#8b5cf6",
  },
  co: {
    label: "CO",
    color: "#10b981",
  },
  o3: {
    label: "O3",
    color: "#f59e0b",
  },
  aqi: {
    label: "AQI",
    color: "#ec4899",
  },
} satisfies ChartConfig;

export default function ChartPollutionTrends({
  pollutionData,
  title = "Air Quality Trends",
}: IChartPollutionTrends) {
  const [timeRange, setTimeRange] = React.useState("10y");

  const filteredData = React.useMemo(() => {
    const currentYear = new Date().getFullYear();
    let yearsToShow = 10;

    if (timeRange === "5y") {
      yearsToShow = 5;
    } else if (timeRange === "3y") {
      yearsToShow = 3;
    }

    return pollutionData.filter((item) => item.year >= currentYear - yearsToShow);
  }, [pollutionData, timeRange]);

  // Get available pollution metrics (exclude 'year')
  const availableMetrics = React.useMemo(() => {
    if (filteredData.length === 0) return [];
    const keys = Object.keys(filteredData[0]).filter(key => key !== 'year' && key !== '_id' && key !== 'cityId');
    return keys;
  }, [filteredData]);

  // Calculate average values
  const averages = React.useMemo(() => {
    if (filteredData.length === 0) return {};

    const sums: Record<string, number> = {};
    availableMetrics.forEach(metric => {
      sums[metric] = filteredData.reduce((acc, item) => acc + (item[metric] || 0), 0) / filteredData.length;
    });

    return sums;
  }, [filteredData, availableMetrics]);

  return (
    <Card className="pt-0 transition-all duration-300 hover:shadow-lg">
      <CardHeader className="flex items-center gap-2 space-y-0 border-b py-5 sm:flex-row">
        <div className="grid flex-1 gap-1">
          <CardTitle>{title}</CardTitle>
          <CardDescription>
            Air pollution metrics over time
          </CardDescription>
        </div>
        <Select value={timeRange} onValueChange={setTimeRange}>
          <SelectTrigger
            className="hidden w-[160px] rounded-lg sm:ml-auto sm:flex"
            aria-label="Select a value"
          >
            <SelectValue placeholder="Last 10 years" />
          </SelectTrigger>
          <SelectContent className="rounded-xl">
            <SelectItem value="10y" className="rounded-lg">
              Last 10 years
            </SelectItem>
            <SelectItem value="5y" className="rounded-lg">
              Last 5 years
            </SelectItem>
            <SelectItem value="3y" className="rounded-lg">
              Last 3 years
            </SelectItem>
          </SelectContent>
        </Select>
      </CardHeader>

      {/* Average Metrics Display */}
      {Object.keys(averages).length > 0 && (
        <div className="grid grid-cols-2 gap-3 px-4 py-4 bg-muted/50 border-b sm:gap-4 sm:px-6 md:grid-cols-3 lg:grid-cols-4">
          {availableMetrics.slice(0, 4).map((metric) => (
            <div key={metric} className="space-y-1 min-w-0">
              <p className="text-xs text-muted-foreground font-medium truncate uppercase">
                Avg. {metric}
              </p>
              <p className="text-lg font-bold sm:text-xl truncate">
                {averages[metric]?.toFixed(1) || '0'}
              </p>
            </div>
          ))}
        </div>
      )}

      <CardContent className="px-2 pt-4 sm:px-6 sm:pt-6">
        <ChartContainer
          config={chartConfig}
          className="aspect-auto h-[350px] w-full"
        >
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={filteredData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="year"
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
                    labelFormatter={(value) => `Year ${value}`}
                  />
                }
              />
              {availableMetrics.map((metric, index) => {
                const colors = ["#ef4444", "#f97316", "#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ec4899"];
                return (
                  <Line
                    key={metric}
                    type="monotone"
                    dataKey={metric}
                    stroke={colors[index % colors.length]}
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    name={metric.toUpperCase()}
                  />
                );
              })}
              <ChartLegend content={<ChartLegendContent />} />
            </LineChart>
          </ResponsiveContainer>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}

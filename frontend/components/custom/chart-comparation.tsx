"use client";

import * as React from "react";
import {
  ComposedChart,
  Line,
  Area,
  CartesianGrid,
  XAxis,
  YAxis,
} from "recharts";

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
import { CityCarsChartData } from "../../views/home";

const chartConfig = {
  cars: {
    label: "Cars",
    color: "#ef4444",
  },
  population: {
    label: "Population",
    color: "#3b82f6",
  },
} satisfies ChartConfig;

interface IChartComparison {
  carsData: CityCarsChartData[];
  populationData: CityCarsChartData[];
  title?: string;
}

export default function ChartComparison({
  carsData,
  populationData,
  title = "Cars vs Population Analysis",
}: IChartComparison) {
  const [timeRange, setTimeRange] = React.useState("10y");

  // Merge data by year
  const mergedData = React.useMemo(() => {
    const dataMap = new Map<
      number,
      { year: number; cars?: number; population?: number }
    >();

    carsData.forEach((item) => {
      dataMap.set(item.year, { year: item.year, cars: item.cars });
    });

    populationData.forEach((item) => {
      const existing = dataMap.get(item.year);
      if (existing) {
        existing.population = item.population;
      } else {
        dataMap.set(item.year, {
          year: item.year,
          population: item.population,
        });
      }
    });

    return Array.from(dataMap.values()).sort((a, b) => a.year - b.year);
  }, [carsData, populationData]);

  // Filter data based on time range
  const filteredData = React.useMemo(() => {
    const currentYear = new Date().getFullYear();
    let yearsToShow = 10;

    if (timeRange === "5y") {
      yearsToShow = 5;
    } else if (timeRange === "3y") {
      yearsToShow = 3;
    }

    return mergedData.filter((item) => item.year >= currentYear - yearsToShow);
  }, [mergedData, timeRange]);

  // Calculate cars per capita ratio using filtered data
  const carsPerCapitaData = React.useMemo(() => {
    return filteredData.map((item) => {
      const ratio =
        item.cars && item.population
          ? (item.cars / item.population) * 1000 // per 1000 people
          : 0;
      return { ...item, ratio };
    });
  }, [filteredData]);

  const avgRatio = React.useMemo(() => {
    const validRatios = carsPerCapitaData.filter((d) => d.ratio > 0);
    if (validRatios.length === 0) return 0;
    return (
      validRatios.reduce((sum, d) => sum + d.ratio, 0) / validRatios.length
    );
  }, [carsPerCapitaData]);

  // Calculate ratio change over time
  const ratioChange = React.useMemo(() => {
    if (carsPerCapitaData.length < 2) return null;
    const firstRatio = carsPerCapitaData[0].ratio;
    const lastRatio = carsPerCapitaData[carsPerCapitaData.length - 1].ratio;
    const change = lastRatio - firstRatio;
    const changePercent = firstRatio !== 0 ? (change / firstRatio) * 100 : 0;
    return {
      change,
      changePercent,
      trend: changePercent > 0 ? "up" : changePercent < 0 ? "down" : "stable",
    };
  }, [carsPerCapitaData]);

  return (
    <Card className="pt-0 transition-all duration-300 hover:shadow-xl border-2">
      <CardHeader className="flex items-center gap-2 space-y-0 border-b py-5 bg-gradient-to-r from-red-50 to-blue-50 sm:flex-row">
        <div className="grid flex-1 gap-1">
          <CardTitle>{title}</CardTitle>
          <CardDescription>
            Comparative view of vehicle ownership and population trends
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

      {/* Key Insight */}
      <div className="px-4 py-4 bg-gradient-to-r from-orange-50 to-blue-50 border-b sm:px-6 sm:py-6">
        <div className="grid gap-4 sm:gap-6 md:grid-cols-2">
          <div className="space-y-2 min-w-0">
            <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wide sm:text-sm">
              Average Cars per 1,000 People
            </p>
            <p className="text-3xl font-extrabold bg-gradient-to-r from-orange-600 to-blue-600 bg-clip-text text-transparent sm:text-4xl">
              {avgRatio.toFixed(0)}
            </p>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Vehicle ownership density in the selected period
            </p>
          </div>
          {ratioChange && (
            <div className="space-y-2 min-w-0">
              <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wide sm:text-sm">
                Car Ownership Change
              </p>
              <div className="flex items-baseline gap-2">
                <p
                  className={`text-3xl font-extrabold sm:text-4xl ${
                    ratioChange.trend === "up"
                      ? "text-green-600"
                      : ratioChange.trend === "down"
                      ? "text-red-600"
                      : "text-gray-600"
                  }`}
                >
                  {ratioChange.changePercent >= 0 ? "+" : ""}
                  {ratioChange.changePercent.toFixed(1)}%
                </p>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed break-words">
                From {carsPerCapitaData[0].ratio.toFixed(0)} to{" "}
                {carsPerCapitaData[carsPerCapitaData.length - 1].ratio.toFixed(
                  0
                )}{" "}
                cars per 1,000 people
              </p>
            </div>
          )}
        </div>
      </div>

      <CardContent className="px-2 pt-4 sm:px-6 sm:pt-6">
        <ChartContainer
          config={chartConfig}
          className="aspect-auto h-[300px] w-full"
        >
          <ComposedChart data={filteredData}>
            <defs>
              <linearGradient
                id="gradient-cars-comp"
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop offset="0%" stopColor="#ef4444" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#ef4444" stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="year"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
            />
            <YAxis
              yAxisId="left"
              orientation="left"
              stroke="#ef4444"
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${(value / 1000).toFixed(0)}K`}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              stroke="#3b82f6"
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${(value / 1000).toFixed(0)}K`}
            />
            <ChartTooltip
              content={
                <ChartTooltipContent
                  labelFormatter={(value) => `Year ${value}`}
                  formatter={(value, name) => [
                    typeof value === "number" ? value.toLocaleString() : value,
                    name === "cars" ? "Cars" : "Population",
                  ]}
                />
              }
            />
            <Area
              yAxisId="left"
              dataKey="cars"
              type="monotone"
              fill="url(#gradient-cars-comp)"
              stroke="#ef4444"
              strokeWidth={2}
            />
            <Line
              yAxisId="right"
              dataKey="population"
              type="monotone"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ fill: "#3b82f6", r: 4 }}
            />
            <ChartLegend content={<ChartLegendContent />} />
          </ComposedChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}

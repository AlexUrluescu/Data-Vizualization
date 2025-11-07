"use client";

import * as React from "react";
import { Area, AreaChart, CartesianGrid, XAxis } from "recharts";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CityCarsChartData } from "../../views/home";
import { calculateChartMetrics, formatNumber, formatPercent } from "@/lib/utils";

const chartConfig = {
  cars: {
    label: "Cars",
    color: "hsl(var(--chart-1))",
  },
  population: {
    label: "Population",
    color: "hsl(var(--chart-2))",
  },
} satisfies ChartConfig;

interface IChartAreaInteractive {
  cityCarsState: CityCarsChartData[];
  title: string;
  type: "cars" | "population" | "parking";
}

export default function ChartAreaInteractive({
  cityCarsState,
  title,
  type,
}: IChartAreaInteractive) {
  const [timeRange, setTimeRange] = React.useState("10y");

  const filteredData = cityCarsState.filter((item) => {
    const year = item.year;
    const currentYear = new Date().getFullYear();

    let yearsToShow = 10;
    if (timeRange === "5y") {
      yearsToShow = 5;
    } else if (timeRange === "3y") {
      yearsToShow = 3;
    }

    return year >= currentYear - yearsToShow;
  });

  // Dynamic gradient colors based on chart type
  const getGradientColors = () => {
    switch (type) {
      case "cars":
        return {
          start: "#ef4444", // red (environmental concern)
          middle: "#f97316", // orange
          end: "#fb923c", // light orange
        };
      case "population":
        return {
          start: "#3b82f6", // blue
          middle: "#60a5fa", // light blue
          end: "#93c5fd", // lighter blue
        };
      case "parking":
        return {
          start: "#10b981", // green
          middle: "#34d399", // light green
          end: "#6ee7b7", // lighter green
        };
      default:
        return {
          start: "#8b5cf6", // purple
          middle: "#a78bfa",
          end: "#c4b5fd",
        };
    }
  };

  const colors = getGradientColors();
  const metrics = calculateChartMetrics(filteredData);

  const TrendIcon =
    metrics?.trend === "up" ? TrendingUp :
    metrics?.trend === "down" ? TrendingDown : Minus;

  // Get starting value from filtered data
  const startingValue = filteredData.length > 0
    ? Object.values(filteredData[0]).find(v => typeof v === "number" && v !== filteredData[0].year) || 0
    : 0;

  return (
    <Card className="pt-0 transition-all duration-300 hover:shadow-lg">
      <CardHeader className="flex items-center gap-2 space-y-0 border-b py-5 sm:flex-row">
        <div className="grid flex-1 gap-1">
          <CardTitle>{title} Chart - Interactive</CardTitle>
          <CardDescription>
            Showing total {title} over the years
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

      {/* Key Metrics Display */}
      {metrics && (
        <div className="grid grid-cols-2 gap-3 px-4 py-4 bg-muted/50 border-b sm:gap-4 sm:px-6 lg:grid-cols-4">
          <div className="space-y-1 min-w-0">
            <p className="text-xs text-muted-foreground font-medium truncate">Latest ({filteredData[filteredData.length - 1]?.year})</p>
            <p className="text-xl font-bold sm:text-2xl truncate">{formatNumber(metrics.total)}</p>
          </div>
          <div className="space-y-1 min-w-0">
            <p className="text-xs text-muted-foreground font-medium truncate">Starting ({filteredData[0]?.year})</p>
            <p className="text-xl font-bold text-muted-foreground sm:text-2xl truncate">{formatNumber(startingValue)}</p>
          </div>
          <div className="space-y-1 min-w-0">
            <p className="text-xs text-muted-foreground font-medium truncate">Net Change</p>
            <div className="flex flex-col gap-1">
              <p className={`text-xl font-bold sm:text-2xl whitespace-nowrap ${
                metrics.trend === "up" ? "text-green-600" :
                metrics.trend === "down" ? "text-red-600" : "text-gray-600"
              }`}>
                {formatPercent(metrics.changePercent)}
              </p>
              <div className={`flex items-center gap-1 text-xs font-semibold ${
                metrics.trend === "up" ? "text-green-600" :
                metrics.trend === "down" ? "text-red-600" : "text-gray-600"
              }`}>
                <TrendIcon className="h-3 w-3 sm:h-4 sm:w-4" />
                <span className="whitespace-nowrap">{metrics.change >= 0 ? "+" : ""}{formatNumber(metrics.change)}</span>
              </div>
            </div>
          </div>
          <div className="space-y-1 min-w-0">
            <p className="text-xs text-muted-foreground font-medium truncate">Avg. Annual Growth</p>
            <p className={`text-xl font-bold sm:text-2xl ${
              metrics.trend === "up" ? "text-green-600" :
              metrics.trend === "down" ? "text-red-600" : "text-gray-600"
            }`}>
              {formatPercent(metrics.growthRate)}
            </p>
          </div>
        </div>
      )}

      <CardContent className="px-2 pt-4 sm:px-6 sm:pt-6">
        <ChartContainer
          config={chartConfig}
          className="aspect-auto h-[300px] w-full"
        >
          <AreaChart data={filteredData}>
            <defs>
              {/* Dynamic gradient based on chart type */}
              <linearGradient id={`gradient-${type}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={colors.start} stopOpacity={0.8} />
                <stop offset="50%" stopColor={colors.middle} stopOpacity={0.6} />
                <stop offset="100%" stopColor={colors.end} stopOpacity={0.4} />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="year"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              interval="preserveStartEnd"
            />
            <ChartTooltip
              cursor={false}
              content={
                <ChartTooltipContent
                  labelFormatter={(value) => `Year ${value}`}
                  indicator="dot"
                />
              }
            />
            <Area
              dataKey={type} // Dynamic: cars, population, or parking
              type="natural"
              fill={`url(#gradient-${type})`}
              stroke={colors.start}
              strokeWidth={2}
              stackId="a"
            />
            <ChartLegend content={<ChartLegendContent />} />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}

"use client";

import * as React from "react";
import { Area, AreaChart, CartesianGrid, XAxis } from "recharts";

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

  return (
    <Card className="pt-0">
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
      <CardContent className="px-2 pt-4 sm:px-6 sm:pt-6">
        <ChartContainer
          config={chartConfig}
          className="aspect-auto h-[250px] w-full"
        >
          <AreaChart data={filteredData}>
            <defs>
              {/* Gradient green → yellow → red */}
              <linearGradient id="gradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="red" stopOpacity={0.8} />
                <stop offset="50%" stopColor="yellow" stopOpacity={0.8} />
                <stop offset="100%" stopColor="green" stopOpacity={0.8} />
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
              dataKey={type} // Dynamic: cars or population
              type="natural"
              fill="url(#gradient)"
              stroke="var(--color-desktop)"
              stackId="a"
            />
            <ChartLegend content={<ChartLegendContent />} />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}

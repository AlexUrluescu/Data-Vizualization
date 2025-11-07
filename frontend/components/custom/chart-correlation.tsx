"use client";

import * as React from "react";
import { LineChart, Line, CartesianGrid, XAxis, YAxis, ResponsiveContainer, Legend, Tooltip } from "recharts";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CityCarsChartData } from "../../views/home";
import { PollutionData } from "./chart-pollution-trends";

interface IChartCorrelation {
  carsData: CityCarsChartData[];
  populationData: CityCarsChartData[];
  parkingData: CityCarsChartData[];
  pollutionData?: PollutionData[] | null;
}

type CorrelationDataPoint = {
  year: number;
  cars: number;
  population: number;
  parking: number;
  pollutionIndex?: number;
  carsPerCapita: number;
  parkingRatio: number;
};

export default function ChartCorrelation({
  carsData,
  populationData,
  parkingData,
  pollutionData,
}: IChartCorrelation) {
  const [timeRange, setTimeRange] = React.useState("10y");

  // Merge all data by year
  const mergedData = React.useMemo(() => {
    const dataMap = new Map<number, Partial<CorrelationDataPoint>>();

    // Add cars data
    carsData.forEach((item) => {
      dataMap.set(item.year, { ...dataMap.get(item.year), year: item.year, cars: item.cars || 0 });
    });

    // Add population data
    populationData.forEach((item) => {
      const existing = dataMap.get(item.year);
      dataMap.set(item.year, { ...existing, year: item.year, population: item.population || 0 });
    });

    // Add parking data
    parkingData.forEach((item) => {
      const existing = dataMap.get(item.year);
      dataMap.set(item.year, { ...existing, year: item.year, parking: item.parking || 0 });
    });

    // Add average pollution index if available
    if (pollutionData && pollutionData.length > 0) {
      pollutionData.forEach((item) => {
        const existing = dataMap.get(item.year);
        // Calculate average of all pollution metrics
        const metrics = Object.keys(item).filter(key => key !== 'year' && key !== '_id' && key !== 'cityId');
        const avgPollution = metrics.length > 0
          ? metrics.reduce((sum, key) => sum + (item[key] as number), 0) / metrics.length
          : 0;

        dataMap.set(item.year, { ...existing, year: item.year, pollutionIndex: avgPollution });
      });
    }

    // Calculate derived metrics
    const finalData: CorrelationDataPoint[] = Array.from(dataMap.values()).map(item => {
      const cars = item.cars || 0;
      const population = item.population || 1; // Avoid division by zero
      const parking = item.parking || 0;

      return {
        year: item.year!,
        cars,
        population,
        parking,
        pollutionIndex: item.pollutionIndex,
        carsPerCapita: (cars / population) * 1000, // Per 1000 people
        parkingRatio: parking > 0 ? (cars / parking) * 100 : 0, // Parking utilization %
      };
    }).sort((a, b) => a.year - b.year);

    return finalData;
  }, [carsData, populationData, parkingData, pollutionData]);

  // Filter by time range
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

  // Calculate correlations
  const correlations = React.useMemo(() => {
    if (filteredData.length < 2) return null;

    const latest = filteredData[filteredData.length - 1];
    const first = filteredData[0];

    return {
      carsGrowth: ((latest.cars - first.cars) / first.cars) * 100,
      populationGrowth: ((latest.population - first.population) / first.population) * 100,
      parkingGrowth: ((latest.parking - first.parking) / first.parking) * 100,
      pollutionChange: latest.pollutionIndex && first.pollutionIndex
        ? ((latest.pollutionIndex - first.pollutionIndex) / first.pollutionIndex) * 100
        : null,
      avgCarsPerCapita: filteredData.reduce((sum, d) => sum + d.carsPerCapita, 0) / filteredData.length,
      avgParkingUtil: filteredData.reduce((sum, d) => sum + d.parkingRatio, 0) / filteredData.length,
    };
  }, [filteredData]);

  return (
    <Card className="pt-0 transition-all duration-300 hover:shadow-xl border-2 border-primary/20">
      <CardHeader className="flex items-center gap-2 space-y-0 border-b py-5 bg-gradient-to-r from-purple-50 via-pink-50 to-orange-50 sm:flex-row">
        <div className="grid flex-1 gap-1">
          <CardTitle className="text-2xl">🔗 Urban Data Correlation Analysis</CardTitle>
          <CardDescription className="text-base">
            Comprehensive view of how cars, population, parking, and pollution interact over time
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

      {/* Key Correlations */}
      {correlations && (
        <div className="grid grid-cols-2 gap-3 px-4 py-4 bg-gradient-to-r from-purple-50/50 to-orange-50/50 border-b sm:gap-4 sm:px-6 md:grid-cols-3 lg:grid-cols-6">
          <div className="space-y-1 min-w-0">
            <p className="text-xs text-muted-foreground font-medium truncate">Cars Growth</p>
            <p className={`text-lg font-bold sm:text-xl ${correlations.carsGrowth > 0 ? 'text-orange-600' : 'text-green-600'}`}>
              {correlations.carsGrowth >= 0 ? '+' : ''}{correlations.carsGrowth.toFixed(1)}%
            </p>
          </div>
          <div className="space-y-1 min-w-0">
            <p className="text-xs text-muted-foreground font-medium truncate">Pop. Growth</p>
            <p className="text-lg font-bold text-blue-600 sm:text-xl">
              {correlations.populationGrowth >= 0 ? '+' : ''}{correlations.populationGrowth.toFixed(1)}%
            </p>
          </div>
          <div className="space-y-1 min-w-0">
            <p className="text-xs text-muted-foreground font-medium truncate">Parking Growth</p>
            <p className={`text-lg font-bold sm:text-xl ${correlations.parkingGrowth > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {correlations.parkingGrowth >= 0 ? '+' : ''}{correlations.parkingGrowth.toFixed(1)}%
            </p>
          </div>
          {correlations.pollutionChange !== null && (
            <div className="space-y-1 min-w-0">
              <p className="text-xs text-muted-foreground font-medium truncate">Pollution Δ</p>
              <p className={`text-lg font-bold sm:text-xl ${correlations.pollutionChange > 0 ? 'text-red-600' : 'text-green-600'}`}>
                {correlations.pollutionChange >= 0 ? '+' : ''}{correlations.pollutionChange.toFixed(1)}%
              </p>
            </div>
          )}
          <div className="space-y-1 min-w-0">
            <p className="text-xs text-muted-foreground font-medium truncate">Avg. Cars/1K</p>
            <p className="text-lg font-bold text-purple-600 sm:text-xl">
              {correlations.avgCarsPerCapita.toFixed(0)}
            </p>
          </div>
          <div className="space-y-1 min-w-0">
            <p className="text-xs text-muted-foreground font-medium truncate">Parking Util.</p>
            <p className={`text-lg font-bold sm:text-xl ${correlations.avgParkingUtil > 100 ? 'text-red-600' : 'text-green-600'}`}>
              {correlations.avgParkingUtil.toFixed(0)}%
            </p>
          </div>
        </div>
      )}

      <CardContent className="px-2 pt-4 sm:px-6 sm:pt-6">
        <div className="space-y-6">
          {/* Main Correlation Chart */}
          <div>
            <h3 className="text-sm font-semibold mb-3 text-muted-foreground">Absolute Values Comparison</h3>
            <div className="h-[350px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={filteredData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.3} />
                  <XAxis
                    dataKey="year"
                    tickLine={false}
                    axisLine={false}
                    tickMargin={8}
                    style={{ fontSize: '12px' }}
                  />
                  <YAxis
                    tickLine={false}
                    axisLine={false}
                    tickMargin={8}
                    style={{ fontSize: '12px' }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(255, 255, 255, 0.95)',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      padding: '12px',
                    }}
                  />
                  <Legend wrapperStyle={{ paddingTop: '20px' }} />
                  <Line
                    type="monotone"
                    dataKey="cars"
                    stroke="#ef4444"
                    strokeWidth={3}
                    dot={{ r: 5, fill: "#ef4444" }}
                    name="Cars"
                    activeDot={{ r: 7 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="population"
                    stroke="#3b82f6"
                    strokeWidth={3}
                    dot={{ r: 5, fill: "#3b82f6" }}
                    name="Population"
                    activeDot={{ r: 7 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="parking"
                    stroke="#10b981"
                    strokeWidth={3}
                    dot={{ r: 5, fill: "#10b981" }}
                    name="Parking Spots"
                    activeDot={{ r: 7 }}
                  />
                  {pollutionData && pollutionData.length > 0 && (
                    <Line
                      type="monotone"
                      dataKey="pollutionIndex"
                      stroke="#8b5cf6"
                      strokeWidth={3}
                      dot={{ r: 5, fill: "#8b5cf6" }}
                      name="Avg. Pollution"
                      activeDot={{ r: 7 }}
                    />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Derived Metrics Chart */}
          <div>
            <h3 className="text-sm font-semibold mb-3 text-muted-foreground">Derived Metrics & Ratios</h3>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={filteredData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.3} />
                  <XAxis
                    dataKey="year"
                    tickLine={false}
                    axisLine={false}
                    tickMargin={8}
                    style={{ fontSize: '12px' }}
                  />
                  <YAxis
                    tickLine={false}
                    axisLine={false}
                    tickMargin={8}
                    style={{ fontSize: '12px' }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(255, 255, 255, 0.95)',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      padding: '12px',
                    }}
                  />
                  <Legend wrapperStyle={{ paddingTop: '20px' }} />
                  <Line
                    type="monotone"
                    dataKey="carsPerCapita"
                    stroke="#ec4899"
                    strokeWidth={3}
                    dot={{ r: 5, fill: "#ec4899" }}
                    name="Cars per 1K People"
                    activeDot={{ r: 7 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="parkingRatio"
                    stroke="#f59e0b"
                    strokeWidth={3}
                    dot={{ r: 5, fill: "#f59e0b" }}
                    name="Parking Utilization %"
                    activeDot={{ r: 7 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Insights */}
        <div className="mt-6 p-4 bg-gradient-to-r from-purple-50 to-orange-50 rounded-lg border border-purple-200">
          <h4 className="text-sm font-semibold text-purple-900 mb-2">📊 Key Insights</h4>
          <ul className="text-xs text-purple-800 space-y-1">
            {correlations && (
              <>
                <li>• Vehicle ownership is {correlations.carsGrowth > correlations.populationGrowth ? 'growing faster' : 'growing slower'} than population growth</li>
                <li>• Average {correlations.avgCarsPerCapita.toFixed(0)} cars per 1,000 residents in this period</li>
                <li>• Parking infrastructure is {correlations.parkingGrowth > correlations.carsGrowth ? 'keeping pace with' : 'falling behind'} vehicle growth</li>
                {correlations.pollutionChange !== null && (
                  <li>• Pollution levels have {correlations.pollutionChange > 0 ? 'increased' : 'decreased'} by {Math.abs(correlations.pollutionChange).toFixed(1)}%</li>
                )}
              </>
            )}
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}

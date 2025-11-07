"use client";

import * as React from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";
import { Car, ParkingSquare, AlertTriangle } from "lucide-react";

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
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { CityCarsChartData } from "../../views/home";
import { formatNumber } from "@/lib/utils";

const chartConfig = {
  utilized: {
    label: "Utilized Parking",
    color: "#ef4444",
  },
  available: {
    label: "Available Parking",
    color: "#10b981",
  },
  deficit: {
    label: "Parking Deficit",
    color: "#f59e0b",
  },
} satisfies ChartConfig;

interface IChartPieParking {
  carsData: CityCarsChartData[];
  parkingData: CityCarsChartData[];
}

export default function ChartPieParking({
  carsData,
  parkingData,
}: IChartPieParking) {
  const pieData = React.useMemo(() => {
    if (!carsData.length || !parkingData.length) return null;

    // Get latest year data
    const latestCars = carsData[carsData.length - 1].cars || 0;
    const latestParking = parkingData[parkingData.length - 1].parking || 0;

    if (latestParking >= latestCars) {
      // Surplus parking
      return {
        hasDeficit: false,
        data: [
          { name: "Utilized Parking", value: latestCars, fill: "#ef4444" },
          { name: "Available Parking", value: latestParking - latestCars, fill: "#10b981" },
        ],
        cars: latestCars,
        parking: latestParking,
        difference: latestParking - latestCars,
        utilizationRate: (latestCars / latestParking) * 100,
      };
    } else {
      // Parking deficit
      return {
        hasDeficit: true,
        data: [
          { name: "Available Parking", value: latestParking, fill: "#10b981" },
          { name: "Parking Deficit", value: latestCars - latestParking, fill: "#f59e0b" },
        ],
        cars: latestCars,
        parking: latestParking,
        difference: latestCars - latestParking,
        utilizationRate: (latestParking / latestCars) * 100,
      };
    }
  }, [carsData, parkingData]);

  if (!pieData) return null;

  const StatusIcon = pieData.hasDeficit ? AlertTriangle : ParkingSquare;

  return (
    <Card className="pt-0 transition-all duration-300 hover:shadow-lg">
      <CardHeader className="flex items-center gap-2 space-y-0 border-b py-5">
        <div className="grid flex-1 gap-1">
          <CardTitle>Parking Capacity Analysis</CardTitle>
          <CardDescription>
            Current parking infrastructure vs. vehicle ownership
          </CardDescription>
        </div>
      </CardHeader>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 gap-4 px-4 py-4 bg-muted/50 border-b sm:grid-cols-3 sm:px-6">
        <div className="space-y-1 min-w-0">
          <div className="flex items-center gap-2">
            <Car className="h-4 w-4 text-red-600" />
            <p className="text-xs text-muted-foreground font-medium">Total Cars</p>
          </div>
          <p className="text-2xl font-bold">{formatNumber(pieData.cars)}</p>
        </div>
        <div className="space-y-1 min-w-0">
          <div className="flex items-center gap-2">
            <ParkingSquare className="h-4 w-4 text-green-600" />
            <p className="text-xs text-muted-foreground font-medium">Parking Spots</p>
          </div>
          <p className="text-2xl font-bold">{formatNumber(pieData.parking)}</p>
        </div>
        <div className="space-y-1 min-w-0">
          <div className="flex items-center gap-2">
            <StatusIcon className={`h-4 w-4 ${pieData.hasDeficit ? 'text-orange-600' : 'text-green-600'}`} />
            <p className="text-xs text-muted-foreground font-medium">
              {pieData.hasDeficit ? 'Deficit' : 'Surplus'}
            </p>
          </div>
          <p className={`text-2xl font-bold ${pieData.hasDeficit ? 'text-orange-600' : 'text-green-600'}`}>
            {pieData.hasDeficit ? '-' : '+'}{formatNumber(pieData.difference)}
          </p>
        </div>
      </div>

      <CardContent className="px-2 pt-4 pb-0 sm:px-6">
        <div className="grid gap-4 md:grid-cols-2">
          {/* Pie Chart */}
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData.data}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="rounded-lg border bg-background p-2 shadow-sm">
                          <div className="grid gap-2">
                            <div className="flex items-center justify-between gap-2">
                              <span className="text-sm text-muted-foreground">
                                {payload[0].name}
                              </span>
                              <span className="text-sm font-bold">
                                {formatNumber(payload[0].value as number)}
                              </span>
                            </div>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Analysis */}
          <div className="flex flex-col justify-center space-y-4">
            <div className="space-y-2">
              <h3 className="text-lg font-semibold">Status Summary</h3>
              {pieData.hasDeficit ? (
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    The city has a <span className="font-semibold text-orange-600">parking deficit</span> of{' '}
                    <span className="font-bold">{formatNumber(pieData.difference)}</span> spots.
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Only <span className="font-bold">{pieData.utilizationRate.toFixed(1)}%</span> of vehicles
                    can be accommodated with current parking infrastructure.
                  </p>
                  <div className="mt-3 p-3 bg-orange-50 rounded-lg border border-orange-200">
                    <p className="text-xs text-orange-800 font-medium">
                      ⚠️ Urgent Action Needed: Consider expanding parking infrastructure or promoting alternative transportation.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    The city has a <span className="font-semibold text-green-600">parking surplus</span> of{' '}
                    <span className="font-bold">{formatNumber(pieData.difference)}</span> spots.
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Current utilization rate is <span className="font-bold">{pieData.utilizationRate.toFixed(1)}%</span>,
                    indicating adequate parking capacity.
                  </p>
                  <div className="mt-3 p-3 bg-green-50 rounded-lg border border-green-200">
                    <p className="text-xs text-green-800 font-medium">
                      ✅ Good Infrastructure: Sufficient parking available for current vehicle population.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

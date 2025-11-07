"use client";
import React, { useState } from "react";
import ChartAreaInteractive from "../components/custom/chart";
import CitiesOptions from "../components/custom/cities-options";
import SibiuTrafficMap from "@/components/custom/map";

type City = {
  _id: string;
  name: string;
  region: string;
};

export type CityCar = {
  _id: string;
  cityId: string;
  amount: number;
  year: number;
  population?: number; // Add population field
};

export type CityCarsChartData = {
  year: number;
  cars: number;
  population: number;
};

interface ICitiesOptions {
  citiesEntities: City[];
}

export default function HomeView({
  citiesEntities,
}: ICitiesOptions): React.ReactElement {
  const [cityCarsChartData, setCityCarsChartData] = useState<CityCarsChartData[] | null>(null);

  const chartData = (cityCars: CityCar[] | null) => {
    if (!cityCars) {
      setCityCarsChartData(null);
      return;
    }

    const carsData: CityCarsChartData[] = cityCars
      .map((data) => ({
        year: data.year,
        cars: data.amount,
        population: data.population || 0, // default 0 if missing
      }))
      .sort((a, b) => a.year - b.year);

    setCityCarsChartData(carsData);
  };

  return (
    <div className="flex flex-col gap-10">
      <CitiesOptions citiesEntities={citiesEntities} chartData={chartData} />
      {cityCarsChartData && (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <ChartAreaInteractive
            title="Cars"
            cityCarsState={cityCarsChartData}
            type="cars"
          />
          <ChartAreaInteractive
            title="Population"
            cityCarsState={cityCarsChartData}
            type="population"
          />
        </div>
      )}
    </div>
  );
}

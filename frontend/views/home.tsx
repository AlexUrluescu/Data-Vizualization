"use client";
import React, { useEffect, useState } from "react";
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
  population?: number;
};

export type CityCarsChartData = {
  year: number;
  cars?: number;
  population?: number;
  parking?: number;
};

interface ICitiesOptions {
  citiesEntities: City[];
}

export default function HomeView({
  citiesEntities,
}: ICitiesOptions): React.ReactElement {
  const [cityCarsChartData, setCityCarsChartData] = useState<
    CityCarsChartData[] | null
  >(null);
  const [cityCarsChartDataPopulation, setCityCarsChartDataPopulation] =
    useState<CityCarsChartData[] | null>(null);
  const [cityCarsChartDataParkings, setCityCarsChartDataParkings] = useState<
    CityCarsChartData[] | null
  >(null);

  const chartData = (cityCars: CityCar[] | null) => {
    if (!cityCars) {
      setCityCarsChartData(null);
      return;
    }

    const carsData: CityCarsChartData[] = cityCars
      .map((data) => ({
        year: data.year,
        cars: data.amount, // Changed from 'amount' to 'cars'
      }))
      .sort((a, b) => a.year - b.year);

    setCityCarsChartData(carsData);
  };

  const chartDataPopulation = (cityCars: CityCar[] | null) => {
    if (!cityCars) {
      setCityCarsChartDataPopulation(null);
      return;
    }

    const populationData: CityCarsChartData[] = cityCars
      .map((data) => ({
        year: data.year,
        population: data.amount || 0, // Map to 'population' field
      }))
      .sort((a, b) => a.year - b.year);

    setCityCarsChartDataPopulation(populationData);
  };

  const chartDataParkings = (cityCars: CityCar[] | null) => {
    if (!cityCars) {
      setCityCarsChartDataParkings(null);
      return;
    }

    const populationData: CityCarsChartData[] = cityCars
      .map((data) => ({
        year: data.year,
        parking: data.amount || 0, // Map to 'population' field
      }))
      .sort((a, b) => a.year - b.year);

    setCityCarsChartDataParkings(populationData);
  };

  useEffect(() => {
    console.log("cityCarsChartDataPopulation", cityCarsChartDataPopulation);
  }, [cityCarsChartDataPopulation]);

  return (
    <div className="flex flex-col gap-10">
      <CitiesOptions
        citiesEntities={citiesEntities}
        chartData={chartData}
        chartDataPopulation={chartDataPopulation}
        chartDataParkings={chartDataParkings}
      />

      {/* Render charts only if both datasets are available */}
      {cityCarsChartData &&
        cityCarsChartDataPopulation &&
        cityCarsChartDataParkings && (
          <div className="flex flex-col gap-5">
            <ChartAreaInteractive
              flex={false}
              title="Cars"
              cityCarsState={cityCarsChartData}
              type="cars"
            />

            <div style={{ display: "flex", gap: 20 }}>
              <ChartAreaInteractive
                flex={true}
                title="Population"
                cityCarsState={cityCarsChartDataPopulation}
                type="population"
              />
              <ChartAreaInteractive
                flex={true}
                title="Parking"
                cityCarsState={cityCarsChartDataParkings}
                type="parking"
              />
            </div>
          </div>
        )}
    </div>
  );
}

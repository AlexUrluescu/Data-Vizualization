"use client";
import React, { useEffect, useState } from "react";
import ChartAreaInteractive from "../components/custom/chart";
import ChartComparison from "../components/custom/chart-comparison";
import ChartPieParking from "../components/custom/chart-pie-parking";
import ChartPollutionTrends, {
  PollutionData,
} from "../components/custom/chart-pollution-trends";
import ChartPollutionBar from "../components/custom/chart-pollution-bar";
import ChartCorrelation from "../components/custom/chart-correlation";
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
  const [pollutionData, setPollutionData] = useState<PollutionData[] | null>(
    null
  );

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

  const chartDataPollution = (pollution: any[] | null) => {
    if (!pollution) {
      setPollutionData(null);
      return;
    }

    const pollutionChartData: PollutionData[] = pollution
      .map((data) => {
        const { year, _id, cityId, ...metrics } = data;
        return {
          year,
          ...metrics,
        };
      })
      .sort((a, b) => a.year - b.year);

    setPollutionData(pollutionChartData);
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
        chartDataPollution={chartDataPollution}
      />

      {/* Render charts only if both datasets are available */}
      {cityCarsChartData &&
        cityCarsChartDataPopulation &&
        cityCarsChartDataParkings && (
          <div className="flex flex-col gap-5">
            {/* Comprehensive Correlation Chart */}
            <ChartCorrelation
              carsData={cityCarsChartData}
              populationData={cityCarsChartDataPopulation}
              parkingData={cityCarsChartDataParkings}
              pollutionData={pollutionData}
            />

            {/* Comparison Chart - Shows relationship between cars and population */}
            <ChartComparison
              carsData={cityCarsChartData}
              populationData={cityCarsChartDataPopulation}
            />

            {/* Individual Charts */}
            <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
              <ChartAreaInteractive
                title="Cars"
                cityCarsState={cityCarsChartData}
                type="cars"
              />
              <ChartAreaInteractive
                title="Population"
                cityCarsState={cityCarsChartDataPopulation}
                type="population"
              />
            </div>

            <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
              <ChartAreaInteractive
                title="Parking Spots"
                cityCarsState={cityCarsChartDataParkings}
                type="parking"
              />
              <ChartPieParking
                carsData={cityCarsChartData}
                parkingData={cityCarsChartDataParkings}
              />
            </div>

            {/* Pollution Charts */}
            {pollutionData && pollutionData.length > 0 && (
              <>
                <h2 className="text-3xl font-bold mt-8 mb-4">
                  Air Quality Analysis
                </h2>
                <div className="grid grid-cols-1 gap-5">
                  <ChartPollutionTrends pollutionData={pollutionData} />
                </div>
              </>
            )}
          </div>
        )}
    </div>
  );
}

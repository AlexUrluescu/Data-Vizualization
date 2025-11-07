"use client";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import React, { useState } from "react";

enum CityType {
  ALL_CITIES = "All",
  BIG_CITIES = "Orașe mari",
  MEDIUM_CITIES = "Orașe medii",
  SMALL_CITIES = "Orașe mici",
}

type City = {
  _id: string;
  name: string;
  region: string;
};

type CityCar = {
  _id: string;
  cityId: string;
  amount: number;
  year: number;
};

interface ICitiesOptions {
  citiesEntities: City[];
  chartData: (cityCars: CityCar[] | null) => void;
  chartDataPopulation: (cityCars: CityCar[] | null) => void;
  chartDataParkings: (cityCars: CityCar[] | null) => void;
}

export default function CitiesOptions({
  citiesEntities,
  chartData,
  chartDataPopulation,
  chartDataParkings,
}: ICitiesOptions): React.ReactElement {
  const [cityType, setCityType] = useState<CityType>(CityType.ALL_CITIES);
  const [cities, setCities] = useState<City[]>(citiesEntities);
  const [selectedCityId, setSelectedCityId] = useState<string | null>(null);

  async function getCarsByCityId(cityId: string) {
    const res = await fetch(
      `http://localhost:5001/api/v1/cars?cityId=${cityId}`,
      {
        cache: "no-store",
      }
    );

    if (!res.ok) {
      throw new Error("Failed to fetch cars");
    }

    const data = await res.json();

    const res2 = await fetch(
      `http://localhost:5001/api/v1/population?cityId=${cityId}`,
      {
        cache: "no-store",
      }
    );

    if (!res.ok) {
      throw new Error("Failed to fetch cars");
    }

    const data2 = await res2.json();

    console.log("data2", data2);

    const res3 = await fetch(
      `http://localhost:5001/api/v1/parking_spots?cityId=${cityId}`,
      {
        cache: "no-store",
      }
    );

    if (!res.ok) {
      throw new Error("Failed to fetch cars");
    }

    const data3 = await res3.json();

    console.log("data3", data3);

    if (selectedCityId === cityId) {
      setSelectedCityId(null);
      chartData(null);
      chartDataPopulation(null);
      chartDataParkings(null);
    } else {
      setSelectedCityId(cityId);
      chartData(data);
      chartDataPopulation(data2);
      chartDataParkings(data3);
    }
  }

  const changeCityType = (type: CityType) => {
    setCityType(type);

    if (type === CityType.ALL_CITIES) {
      setCities(citiesEntities);
    } else if (type === CityType.BIG_CITIES) {
      const big_cities = citiesEntities.filter(
        (city) => city.region === CityType.BIG_CITIES
      );
      setCities(big_cities);
    } else if (type === CityType.MEDIUM_CITIES) {
      const medium_cities = citiesEntities.filter(
        (city) => city.region === CityType.MEDIUM_CITIES
      );
      setCities(medium_cities);
    } else {
      const small_cities = citiesEntities.filter(
        (city) => city.region === CityType.SMALL_CITIES
      );
      setCities(small_cities);
    }
  };

  const handleInputSearch = (e: any) => {
    const value = e.target.value;

    const cities_from_selected_region = citiesEntities.filter(
      (city) => city.region === cityType
    );

    const similar_cities = cities_from_selected_region.filter((city) =>
      city.name.toLowerCase().includes(value.toLowerCase())
    );

    setCities(similar_cities);
  };

  return (
    <div className="flex flex-col items-center gap-10">
      <Input
        onChange={handleInputSearch}
        className="w-4/5 h-11 bg-white"
        type="email"
        placeholder="City"
      />

      {/* <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: 20,
        }}
      >
        <Button
          onClick={() => changeCityType(CityType.ALL_CITIES)}
          style={{
            background: cityType === CityType.ALL_CITIES ? "orange" : "#ededed",
            color: cityType === CityType.ALL_CITIES ? "white" : "black",
            cursor: "pointer",
          }}
        >
          All cities
        </Button>
        <Button
          onClick={() => changeCityType(CityType.BIG_CITIES)}
          style={{
            background: cityType === CityType.BIG_CITIES ? "orange" : "#ededed",
            color: cityType === CityType.BIG_CITIES ? "white" : "black",
            cursor: "pointer",
          }}
        >
          Orașe mari
        </Button>
        <Button
          onClick={() => changeCityType(CityType.MEDIUM_CITIES)}
          style={{
            background:
              cityType === CityType.MEDIUM_CITIES ? "orange" : "#ededed",
            color: cityType === CityType.MEDIUM_CITIES ? "white" : "black",
            cursor: "pointer",
          }}
        >
          Orașe medii
        </Button>
        <Button
          onClick={() => changeCityType(CityType.SMALL_CITIES)}
          style={{
            background:
              cityType === CityType.SMALL_CITIES ? "orange" : "#ededed",
            color: cityType === CityType.SMALL_CITIES ? "white" : "black",
            cursor: "pointer",
          }}
        >
          Orașe mici
        </Button>
      </div> */}

      <div className="flex justify-center gap-4 flex-wrap">
        {cities.length > 0 ? (
          cities.map((city) => (
            <Button
              style={{
                background: selectedCityId === city._id ? "orange" : "#ededed",
                color: selectedCityId === city._id ? "white" : "black",
              }}
              onClick={() => getCarsByCityId("6908d624c8c026b45976c717")}
              key={city._id}
              className="min-w-[10%] transition-all duration-200 hover:brightness-105"
              variant={"outline"}
            >
              {city.name}
            </Button>
          ))
        ) : (
          <div style={{ padding: 50 }}>No available city</div>
        )}
      </div>
    </div>
  );
}
